# This code defines the views for a Django REST Framework API that handles user authentication, child and story management, reading logs, behavior tasks, and other related functionalities. It includes functions for signing up, signing in, and signing out users, as well as viewsets for managing children and stories. The code also contains utility functions for generating story packages using AI, checking the readiness of story pages, sending notification emails when stories are ready, and generating PDFs of stories. The views interact with the database models to create, update, and retrieve data as needed for the API endpoints.
# Import necessary modules and functions from Django, Django REST Framework, and other libraries. This includes modules for handling authentication, database operations, HTTP responses, asynchronous tasks, and serializers for the API. The code also imports custom modules for AI story generation, PDF generation, and performance timing.
import os
import re
from django.conf import settings
import asyncio
import threading
from datetime import timedelta

from asgiref.sync import async_to_sync, sync_to_async
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import close_old_connections
from django.db.models import Count
from django.http import FileResponse
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes, renderer_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from api.ai_adapters import generate_story_package_ai, generate_initial_assets_ai
from api.models import ArtStyle, Behavior, BehaviorTask, Child, Genre, ReadingLog, Story, StoryPage
from api.pdf_service import save_story_pdf

import hashlib
def _text_hash(text: str) -> str:
    return hashlib.md5((text or "").strip().encode("utf-8")).hexdigest()

# The following functions are defined in this module:
from api.serializers import (
    BehaviorTaskCreateSerializer,
    BehaviorTaskSerializer,
    ChildSerializer,
    ReadingLogCreateSerializer,
    ReadingLogSerializer,
    StoryCreateSerializer,
    StorySerializer,
    UserSerializer,
)
from ai_services.orchestrator import StoryOrchestrator
from api.performance_timer import (
    PipelinePerformanceTimer,
    generate_initial_assets_with_timing_and_live_db_progress,
    generate_remaining_assets_with_timing,
)

# The generate_story_package_ai function is an asynchronous function that generates a story package using AI services. It takes a child, behavior, genre, and art style as input and uses the StoryOrchestrator to create a story package based on these parameters. The function returns the generated story package data, which can be used to create a new story in the database or to provide feedback to the user about the generated content.
async def generate_story_package_ai(child, behavior, genre, art_style):
    orchestrator = StoryOrchestrator()

    return await orchestrator.generate_story_package(
        child_name=child.name,
        gender=child.gender,
        appearance=child.appearance_description or "",
        age_group=child.age_group,
        story_type=genre.label or genre.key,
        target_behavior=behavior.label or behavior.key,
        image_style=art_style.key,
    )

# The generate_initial_assets_ai function is an asynchronous function that generates the initial assets for a story using AI services. It takes the story data, child, art style, an optional reference image, and the number of immediate assets to generate as input. The function uses the StoryOrchestrator to generate the initial assets, which may include images and audio for the story pages. The generated assets are returned as part of the updated story data, which can be used to update the story in the database or to provide feedback to the user about the progress of asset generation.
async def generate_initial_assets_ai(
    story_data,
    child,
    art_style,
    reference_image=None,
    immediate_count=3,
):
    orchestrator = StoryOrchestrator()

    return await orchestrator.generate_initial_assets(
        story_data=story_data,
        reference_image=reference_image,
        immediate_count=immediate_count,
    )

# The generate_initial_assets_with_live_db_progress function is an asynchronous function that generates the initial assets for a story while providing live progress updates to the database. It takes the story data, story ID, an optional reference image, and the number of immediate assets to generate as input. The function generates the first few story pages in parallel and updates the corresponding database fields as soon as each asset is ready. This allows the progress endpoint to return live values for both pages with images and pages with audio, providing a more responsive experience for the user while the assets are being generated.
async def generate_initial_assets_with_live_db_progress(
    story_data,
    story_id,
    reference_image=None,
    immediate_count=3,
):
    """
    Generate the first story pages in parallel and update each DB field as soon
    as it is ready.

    This makes the progress endpoint return live values for both:
    - pagesWithImages
    - pagesWithAudio

    Without this, the UI only sees audio progress after all initial assets finish.
    """
    orchestrator = StoryOrchestrator()
    scenes = story_data.get("scenes") or []

    child_name = story_data.get("child_name", "")
    appearance = story_data.get("appearance", "")
    age_group = story_data.get("age_group", "")
    gender = story_data.get("gender", "")
    story_type = story_data.get("story_type", "")
    target_behavior = story_data.get("target_behavior", "")
    image_style = story_data.get("image_style", "")
    seed = story_data.get("character_seed")

    immediate_count = min(immediate_count, len(scenes))

# The function defines an inner function update_page_field that takes a page number and a variable number of fields to update. It cleans the input fields by stripping whitespace and filtering out any fields with None values. If there are valid fields to update, it performs a database update on the StoryPage model for the specified story ID and page number, updating the provided fields. This allows for efficient updates to the story pages in the database as each asset is generated.
    @sync_to_async
    def update_page_field(page_number, **fields):
        clean_fields = {
            key: (value or "").strip()
            for key, value in fields.items()
            if value is not None
        }

        if clean_fields:
            StoryPage.objects.filter(
                story_id=story_id,
                page_number=page_number,
            ).update(**clean_fields)

    async def generate_page(idx):
        scene = scenes[idx]
        page_number = idx + 1

        async def generate_image():
            try:
                image_url = await orchestrator.flux.gen(
                    prompt=scene.get("image_prompt", ""),
                    ref=reference_image,
                    aspect_ratio="1:1",
                    child_name=child_name,
                    appearance=appearance,
                    age_group=age_group,
                    image_style=image_style,
                    gender=gender,
                    story_type=story_type,
                    target_behavior=target_behavior,
                    seed=seed,
                )
            except Exception as e:
                print("INITIAL SCENE IMAGE FAILED:", e)
                image_url = scene.get("image") or ""

            scene["image"] = image_url or scene.get("image") or ""
            await update_page_field(
                page_number,
                illustration_url=scene["image"],
            )

        async def generate_audio():
            try:
                audio_url = await orchestrator.tts.gen(
                    scene.get("narration_text", ""),
                )
            except Exception as e:
                print("INITIAL SCENE AUDIO FAILED:", e)
                audio_url = scene.get("audio") or ""

            scene["audio"] = audio_url or scene.get("audio") or ""
            await update_page_field(
                page_number,
                audio_url=scene["audio"],
                audio_text_hash=_text_hash(scene.get("narration_text", "")),
            )

        await asyncio.gather(generate_image(), generate_audio())

    tasks = [generate_page(idx) for idx in range(immediate_count)]

    if tasks:
        await asyncio.gather(*tasks)

    return story_data

# The generate_remaining_assets_with_timing function is an asynchronous function that generates the remaining assets for a story while measuring the performance of the generation process. It takes the story data, story ID, and an optional reference image as input. The function uses the StoryOrchestrator to generate the remaining assets for the story pages and updates the corresponding database fields as each asset is generated. The PipelinePerformanceTimer is used to measure the time taken for each stage of the asset generation process, allowing for performance analysis and optimization of the AI generation pipeline.
def _reference_image_for_child(child):
    if child.photo:
        try:
            return child.photo.path
        except Exception:
            try:
                return child.photo.url
            except Exception:
                return None
    return None

# The _media_file_exists function is a helper function that checks if a media file exists at the given URL. It first checks if the URL is valid and starts with the MEDIA_URL defined in the settings. If it does, it constructs the file path by replacing the MEDIA_URL with the MEDIA_ROOT and checks if the file exists and has a size greater than 0. This function is used to verify the existence of media files (such as images and audio) before attempting to access them, ensuring that the application can handle missing or invalid media files gracefully.
def _media_file_exists(url: str) -> bool:
    url = (url or "").strip()

    if not url:
        return False

    if not url.startswith(settings.MEDIA_URL):
        return True

    relative_path = url.replace(settings.MEDIA_URL, "", 1)
    file_path = os.path.join(settings.MEDIA_ROOT, relative_path)

    return os.path.exists(file_path) and os.path.getsize(file_path) > 0

# The _reference_image_for_child function is a helper function that retrieves the reference image for a child. It checks if the child has a photo and attempts to return the file path of the photo. If the file path cannot be accessed, it tries to return the URL of the photo. If neither the file path nor the URL can be accessed, it returns None. This function is used to provide a reference image for AI generation when creating story assets based on the child's appearance.
def _page_audio_ready(page: StoryPage) -> bool:
    url = (page.audio_url or "").strip()

    if not url:
        return False

    if not url.startswith(settings.MEDIA_URL):
        return False

    relative_path = url.replace(settings.MEDIA_URL, "", 1)
    file_path = os.path.join(settings.MEDIA_ROOT, relative_path)

    if not os.path.exists(file_path):
        return False

    if os.path.getsize(file_path) < 5000:
        return False

    try:
        with open(file_path, "rb") as f:
            header = f.read(10)

        if not header:
            return False
    except Exception:
        return False

    return True

# The _page_image_ready function is a helper function that checks if the image for a story page is ready. It does this by verifying that the illustration URL for the page is not empty or just whitespace. If the URL is valid, it returns True, indicating that the image is ready; otherwise, it returns False. This function is used to determine if the image assets for a story page have been successfully generated and are available for use in the application.
def _page_image_ready(page: StoryPage) -> bool:
    return bool((page.illustration_url or "").strip())

# The _initial_pages_ready function checks if the initial pages of a story are ready by verifying that the first few pages (up to a specified target) have both their images and audio assets ready. It retrieves the pages of the story that are within the target page number, checks if there are enough pages, and then uses the _page_image_ready and _page_audio_ready helper functions to ensure that each page has its assets ready. If all the initial pages meet these criteria, it returns True; otherwise, it returns False. This function is used to determine if the story is ready for initial reading while the remaining assets are still being generated in the background.
def _initial_pages_ready(story: Story, target: int = 3) -> bool:
    pages = list(
        story.pages
        .filter(page_number__lte=target)
        .order_by("page_number")
    )

    if len(pages) < target:
        return False

    return all(
        _page_image_ready(page) and _page_audio_ready(page)
        for page in pages
    )
# The _story_pages_ready_for_pdf function checks if the pages of a story are ready for PDF generation. It retrieves all the pages of the story and verifies that there are pages available. It also checks if the story's status is "ready" and if the cover URL is valid. Then, it iterates through each page to ensure that both the narration text and illustration URL are valid and not just empty or whitespace. If all these conditions are met, it returns True, indicating that the story pages are ready for PDF generation; otherwise, it returns False. This function is used to determine if the story has all the necessary assets and information to create a PDF version of the story.
def _story_pages_ready_for_pdf(story: Story) -> bool:
    pages = list(story.pages.all().order_by("page_number"))

    if not pages:
        return False

    if story.status != "ready":
        return False

    # PDF يحتاج الغلاف أيضًا
    if not (story.cover_url and story.cover_url.strip()):
        return False

    for page in pages:
        if not (page.narration_text and page.narration_text.strip()):
            return False

        if not (page.illustration_url and page.illustration_url.strip()):
            return False

    return True

# The _story_progress_payload function generates a payload containing the progress information of a story. It takes a Story object as input and calculates various metrics such as the total number of pages, the number of pages with images and audio, and the target number of initial pages. Based on the story's status and these metrics, it determines the current stage of the story generation process and constructs a message to provide feedback to the user. The function returns a dictionary containing the story's ID, status, stage, message, title, page counts, cover readiness, and PDF status, which can be used to inform the user about the progress of their story.
def _story_progress_payload(story: Story):
    pages = list(story.pages.all())
    total_pages = len(pages)
    pages_with_images = sum(1 for page in pages if _page_image_ready(page))
    pages_with_audio = sum(1 for page in pages if _page_audio_ready(page))
    target_initial = min(3, total_pages) if total_pages else 3

    if story.status == "failed":
        stage = "failed"
        message = "تعذر إنشاء القصة"
    elif story.status == "queued":
        stage = "queued"
        message = "تم استلام طلبك"
    elif story.status == "generating_story":
        stage = "writing"
        message = "نكتب القصة الآن"
    elif story.status == "generating_images":
        if pages_with_images >= target_initial and pages_with_audio >= target_initial:
            stage = "finalizing"
            message = "نجهز الصفحات الأولى للقراءة"
        elif total_pages > 0:
            stage = "initial_assets"
            message = f"نولد أول {target_initial} صفحات"
        else:
            stage = "structuring"
            message = "نقسم القصة إلى صفحات"
    else:
        if (
            total_pages
            and pages_with_images >= total_pages
            and pages_with_audio >= total_pages
            and story.cover_url
        ):
            stage = "complete"
            message = "اكتمل كل شيء"
        else:
            stage = "background"
            message = "أول الصفحات جاهزة، ونكمل الباقي في الخلفية"

    # في حالة وجود خطأ في توليد صورة أو صوت لصفحة، نظهر المرحلة الحالية بدلاً من الانتقال إلى "اكتمل" حتى يتم إصلاح المشكلة أو يتم إعلام المستخدم بفشل القصة.
    return {
        "id": story.id,
        "status": story.status,
        "stage": stage,
        "message": message,
        "title": story.title,
        "totalPages": total_pages,
        "pagesWithImages": pages_with_images,
        "pagesWithAudio": pages_with_audio,
        "initialPagesTarget": target_initial,
        "coverReady": bool(story.cover_url),
        "pdfStatus": story.pdf_status,
        "pdfReady": story.pdf_status == "ready" and bool(story.pdf_file),
        "pdfUrl": story.pdf_file.url if story.pdf_file else "",
    }


def _send_story_ready_email(story):
    try:
        user = story.user
        child_name = story.child.name
        send_mail(
            subject=f"{child_name}'s story is ready to read!",
            message=(
                f"Hi {user.first_name or user.username},\n\n"
                f'The story "{story.title}" for {child_name} is now ready. '
                f"Open the app to start reading!\n\n"
                f"— Gheras"
            ),
            from_email=None,
            recipient_list=[user.email],
            fail_silently=True,
        )
    except Exception:
        pass

def _wait_until_story_ready_for_pdf(story_id: int, timeout_seconds: int = 180):
    import time

    start = time.time()

    while time.time() - start < timeout_seconds:
        story = Story.objects.get(id=story_id)

        if _story_pages_ready_for_pdf(story):
            return story

        Story.objects.filter(id=story_id).update(
            pdf_status="generating",
            pdf_progress=20,
            pdf_error="Waiting for story images and cover to finish...",
        )

        time.sleep(2)

    raise Exception("Timed out waiting for story images and cover to finish")

# The _generate_story_pdf_background function is a background task that generates a PDF version of a story. It takes the story ID as input and performs the PDF generation process while updating the story's PDF status and progress in the database. The function first sets the PDF status to "generating" and then waits until the story is ready for PDF generation by checking if all the necessary assets are available. Once the story is ready, it calls the save_story_pdf function to create the PDF file. If any errors occur during this process, it catches the exception and updates the PDF status to "failed" with the error message. Finally, it ensures that database connections are properly closed after the operation is complete.
def _generate_story_pdf_background(story_id: int):
    close_old_connections()

    try:
        story = Story.objects.get(id=story_id)

        story.pdf_status = "generating"
        story.pdf_progress = 5
        story.pdf_error = ""
        story.save(update_fields=["pdf_status", "pdf_progress", "pdf_error"])

        story = _wait_until_story_ready_for_pdf(story_id)

        story.pdf_progress = 30
        story.pdf_error = ""
        story.save(update_fields=["pdf_progress", "pdf_error"])

        save_story_pdf(story)

    except Exception as e:
        print("PDF BACKGROUND GENERATION FAILED:", e)

        try:
            Story.objects.filter(id=story_id).update(
                pdf_status="failed",
                pdf_progress=0,
                pdf_error=str(e),
            )
        except Exception:
            pass

    finally:
        close_old_connections()

# The _run_story_pipeline function is a comprehensive function that orchestrates the entire process of generating a story based on the provided parameters. It handles the creation and updating of the story and its pages in the database, manages the generation of story content and assets using AI services, and tracks the performance of each stage of the pipeline using a PipelinePerformanceTimer. The function also includes error handling to ensure that any issues during the generation process are properly logged and that the story's status is updated accordingly. Additionally, it sends an email notification to the user when the story is ready for reading.
def _run_story_pipeline(
    story_id: int,
    child_id: int,
    genre_key: str,
    art_style_key: str,
    behavior_key: str,
    custom_behavior: str = "",
):
    close_old_connections()
    timer = None

    # We wrap the entire pipeline in a try-except block to catch any unexpected errors and ensure that the story status is updated to "failed" if something goes wrong. This helps provide feedback to the user and allows for better error tracking and debugging.
    try:
        story = Story.objects.get(id=story_id)
        child = Child.objects.get(id=child_id)
        genre = Genre.objects.get(key=genre_key)
        art_style = ArtStyle.objects.get(key=art_style_key)

        if behavior_key == "other":
            class _CustomBehavior:
                key = "other"
                label = custom_behavior or "أخرى"

            behavior = _CustomBehavior()
        else:
            behavior = Behavior.objects.get(key=behavior_key)

        timer = PipelinePerformanceTimer(
            story_id=story.id,
            child_name=child.name,
            age_group=child.age_group,
            image_style=art_style.key,
            story_type=genre.label or genre.key,
            target_behavior=behavior.label or behavior.key,
        )

        reference_image = _reference_image_for_child(child)

        story.status = "generating_story"
        story.pdf_status = "pending"
        story.save(update_fields=["status", "pdf_status"])

        # We generate the story package (which includes the story structure and text) in a synchronous manner while measuring the time taken for this stage. This allows us to provide feedback to the user about the progress of story generation and to track the performance of this critical stage in the pipeline.
        with timer.measure_sync("LLM story generation"):
            story_data = async_to_sync(generate_story_package_ai)(
                child,
                behavior,
                genre,
                art_style,
            )

        # After generating the story package, we update the story's title, raw JSON data, and status in the database. We also clear any existing story pages to prepare for the new pages that will be generated based on the new story data. This ensures that the database reflects the latest state of the story and that any previous data is removed to avoid confusion or conflicts with the new content.
        story.title = story_data.get("title") or "قصة"
        story.raw_story_json = story_data
        story.status = "generating_images"
        story.pdf_status = "pending"
        story.save(update_fields=["title", "raw_story_json", "status", "pdf_status"])

        StoryPage.objects.filter(story=story).delete()

        # We create the initial story pages in the database based on the scenes defined in the generated story data. This sets up the structure for the story and allows us to update each page with its corresponding assets (images and audio) as they are generated. By creating the pages upfront, we can provide a more seamless experience for the user as they can see the progress of each page being populated with its content.
        for page_number, scene in enumerate(story_data.get("scenes", []), start=1):
            StoryPage.objects.create(
                story=story,
                page_number=page_number,
                narration_text=scene.get("narration_text") or "",
                illustration_url="",
                audio_url="",
                audio_text_hash="",
            )

        initial_target = min(3, len(story_data.get("scenes", [])))
        timer.configure_story_counts(
            total_scenes=len(story_data.get("scenes", [])),
            initial_pages_target=initial_target,
        )

        story_data = async_to_sync(generate_initial_assets_with_timing_and_live_db_progress)(
            story_data=story_data,
            story_id=story.id,
            timer=timer,
            reference_image=reference_image,
            immediate_count=initial_target,
        )

        import time

        initial_ready = False

        for _ in range(2):
            story.refresh_from_db()

            initial_ready = _initial_pages_ready(
                story,
                target=initial_target,
            )

            if initial_ready:
                break

            time.sleep(1)

        story.raw_story_json = story_data

        if initial_ready:
            timer.mark_first_viewable_ready()
            story.status = "ready"
            story.pdf_status = "pending"
            story.save(update_fields=["raw_story_json", "status", "pdf_status"])
            _send_story_ready_email(story)
        else:
            story.status = "generating_images"
            story.pdf_status = "pending"
            story.save(update_fields=["raw_story_json", "status", "pdf_status"])

        updated_story = asyncio.run(
            generate_remaining_assets_with_timing(
                story_data=story_data,
                timer=timer,
                reference_image=reference_image,
                start_index=3,
            )
        )

        for idx, scene in enumerate(updated_story.get("scenes", []), start=1):
            update_fields = {}
                        
            current_page = StoryPage.objects.filter(
            story=story,
            page_number=idx,
            ).first()

            if scene.get("narration_text"):
                new_narration_text = (
                    scene.get("narration_text") or ""
                ).strip()
                
                update_fields["narration_text"] = new_narration_text
                
                # If narration_text changed, invalidate old cached audio.
                # This prevents TTS from reading an old version while UI shows the new text.
                
                if (
                    current_page
                    and current_page.narration_text.strip() != new_narration_text
               ):
                   update_fields["audio_url"] = ""
                   update_fields["audio_text_hash"] = ""

            # If image or audio generation failed for a page, we don't want to overwrite it with an empty value. This allows the UI to still show the existing image/audio for that page and prevents it from looking broken. The page will be retried in the background until it succeeds, at which point the new value will be updated in the DB.
            if scene.get("image"):
                update_fields["illustration_url"] = (
                    scene.get("image") or ""
                ).strip()

            if scene.get("audio"):
                update_fields["audio_url"] = (
                    scene.get("audio") or ""
                ).strip()
                
                update_fields["audio_text_hash"] = _text_hash(
                    scene.get("narration_text") or (
                        current_page.narration_text if current_page else ""
                    )
                )

            if update_fields:
                StoryPage.objects.filter(
                    story=story,
                    page_number=idx,
                ).update(**update_fields)

        cover_image = (updated_story.get("cover_image") or "").strip()

        story.raw_story_json = updated_story

        if cover_image:
            story.cover_url = cover_image[:1000]

        story.save(update_fields=["raw_story_json", "cover_url"])

        story.refresh_from_db()

        if story.status != "ready":
            all_pages = list(story.pages.all().order_by("page_number"))
            all_ready = all(
                _page_image_ready(page) and _page_audio_ready(page)
                for page in all_pages
            )

            if all_ready:
                story.status = "ready"
                story.pdf_status = "pending"
                story.save(update_fields=["status", "pdf_status"])
                _send_story_ready_email(story)

        if _story_pages_ready_for_pdf(story):
            story.pdf_status = "pending"
            story.save(update_fields=["pdf_status"])

        if timer is not None:
            timer.finish(status="completed")

    # By catching a broad exception here, we can ensure that any unexpected errors during the story generation process are logged and that the story's status is updated to "failed" to provide feedback to the user. This helps improve the robustness of the application and allows for better error tracking and debugging.
    except Exception as e:
        print("STORY PIPELINE FAILED:", e)

        if timer is not None:
            timer.finish(status="failed", error_message=str(e))

        try:
            story = Story.objects.get(id=story_id)
            story.status = "failed"
            story.pdf_status = "failed"
            story.save(update_fields=["status", "pdf_status"])
        except Exception:
            pass

    finally:
        close_old_connections()

# Define the different types of stories that can be generated
STORY_TYPES = [
    {
        "id": 1,
        "key": "educational",
        "label": "تعليمية",
        "icon": "GraduationCap",
        "description": "تعلم مفاهيم جديدة بطريقة ممتعة",
    },
    {
        "id": 2,
        "key": "fantasy",
        "label": "خيال",
        "icon": "Sparkles",
        "description": "عوالم وشخصيات خيالية",
    },
    {
        "id": 3,
        "key": "adventure",
        "label": "مغامرة",
        "icon": "Compass",
        "description": "قصص مليئة بالمغامرات والاكتشاف",
    },
    {
        "id": 4,
        "key": "space",
        "label": "فضاء",
        "icon": "Rocket",
        "description": "رحلات إلى الفضاء والكواكب",
    },
    {
        "id": 5,
        "key": "nature",
        "label": "طبيعة",
        "icon": "TreePine",
        "description": "استكشاف الطبيعة والحيوانات",
    },
    {
        "id": 6,
        "key": "social",
        "label": "اجتماعية",
        "icon": "Users",
        "description": "مهارات التواصل والعلاقات",
    },
]

# The STORY_TYPES variable is a list of dictionaries that defines different types of stories that can be generated. Each dictionary represents a story type and contains the following keys:
ART_STYLES = [
    {
        "id": 1,
        "key": "storybook",
        "label": "كتاب أطفال",
        "previewUrl": "",
        "description": "أسلوب كتب الأطفال الكلاسيكي",
    },
    {
        "id": 2,
        "key": "cartoon",
        "label": "كرتون",
        "previewUrl": "",
        "description": "رسومات كرتونية مرحة وملونة",
    },
    {
        "id": 3,
        "key": "watercolor",
        "label": "ألوان مائية",
        "previewUrl": "",
        "description": "رسومات ناعمة بألوان مائية",
    },
    {
        "id": 4,
        "key": "paper",
        "label": "قص ولصق",
        "previewUrl": "",
        "description": "أسلوب القص واللصق الفني",
    },
    {
        "id": 5,
        "key": "pixel",
        "label": "بكسل آرت",
        "previewUrl": "",
        "description": "رسومات رقمية بأسلوب البكسل",
    },
    {
        "id": 6,
        "key": "anime",
        "label": "أنمي",
        "previewUrl": "",
        "description": "رسومات بأسلوب الأنمي الياباني",
    },
]


BEHAVIORS = [
    {
        "id": 1,
        "key": "kindness",
        "label": "اللطف",
        "icon": "Heart",
        "description": "التعامل بلطف مع الآخرين",
    },
    {
        "id": 2,
        "key": "courage",
        "label": "الشجاعة",
        "icon": "Shield",
        "description": "تعزيز الثقة بالنفس والشجاعة",
    },
    {
        "id": 3,
        "key": "honesty",
        "label": "الصدق",
        "icon": "Star",
        "description": "أهمية قول الحقيقة دائمًا",
    },
    {
        "id": 4,
        "key": "sharing",
        "label": "المشاركة",
        "icon": "HandHeart",
        "description": "تعلم مشاركة الأشياء مع الآخرين",
    },
    {
        "id": 5,
        "key": "patience",
        "label": "الصبر",
        "icon": "Clock",
        "description": "التحلي بالصبر وعدم الاستعجال",
    },
    {
        "id": 6,
        "key": "responsibility",
        "label": "المسؤولية",
        "icon": "ClipboardCheck",
        "description": "تحمل المسؤولية والاعتماد على النفس",
    },
    {
        "id": 7,
        "key": "gratitude",
        "label": "الامتنان",
        "icon": "Gift",
        "description": "تقدير الأشياء الجيدة في الحياة والشكر",
    },
    {
        "id": 8,
        "key": "empathy",
        "label": "التعاطف",
        "icon": "Heart",
        "description": "فهم مشاعر الآخرين والتعاطف معهم",
    },
    {
        "id": 9,
        "key": "other",
        "label": "أخرى",
        "icon": "PenLine",
        "description": "اكتب السلوك الذي تريده يدويًا",
    }
]

# The signup function is an API endpoint that allows users to create a new account. It takes the user's name, email, and password from the request data, validates the input, and checks if the email already exists in the database. If the input is valid and the email is unique, it creates a new user account using Django's built-in user model, generates an authentication token for the user, and returns a response containing the token and the serialized user data. If there are any issues with the input or if the email already exists, it returns an appropriate error response with a status code of 400 (Bad Request).
@api_view(["POST"])
@permission_classes([AllowAny])
def signup(request):
    name = request.data.get("name", "")
    email = (request.data.get("email") or "").strip().lower()
    password = request.data.get("password") or ""

    if not email or not password:
        return Response({"error": "Email and password required"}, status=400)

    if not email.endswith("@gmail.com"):
        return Response({"error": "يجب أن يكون البريد الإلكتروني من Gmail فقط."}, status=400,)

    password_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$"

    if not re.match(password_pattern, password):
        return Response(
        {
            "error": "كلمة المرور يجب أن تحتوي على 8 أحرف على الأقل، وحرف كبير، وحرف صغير، ورقم."
        },
        status=400,
    )

    if User.objects.filter(email=email).exists():
        return Response({"error": "Email already exists"}, status=400)

    user = User.objects.create_user(
        username=email,
        email=email,
        password=password,
        first_name=name,
    )

    token, _ = Token.objects.get_or_create(user=user)

    return Response(
        {
            "token": token.key,
            "user": UserSerializer(user).data,
        },
        status=201,
    )

# The signin function is an API endpoint that allows users to sign in to their account. It takes the user's email and password from the request data, authenticates the user using Django's built-in authentication system, and if the credentials are valid, it generates or retrieves an authentication token for the user. The function then returns a response containing the authentication token and the serialized user data. If the credentials are invalid, it returns an error response with a status code of 401 (Unauthorized).
@api_view(["POST"])
@permission_classes([AllowAny])
def signin(request):
    email = request.data.get("email")
    password = request.data.get("password")

    user = authenticate(username=email, password=password)

    if not user:
        return Response({"error": "Invalid credentials"}, status=401)

    token, _ = Token.objects.get_or_create(user=user)

    return Response(
        {
            "token": token.key,
            "user": UserSerializer(user).data,
        }
    )

# The signout function is an API endpoint that allows authenticated users to sign out of their account. When a POST request is made to this endpoint, it deletes the authentication token associated with the user, effectively logging them out. The function returns a response with a status code of 204 (No Content) to indicate that the sign-out process was successful and that there is no additional content to return in the response body.
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def signout(request):
    request.user.auth_token.delete()
    return Response(status=204)

# The me function is an API endpoint that allows authenticated users to retrieve their own user information. When a GET request is made to this endpoint, it returns a response containing the serialized data of the currently authenticated user. This allows users to access their profile information and any relevant details associated with their account.
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user).data)

# The ChildViewSet is a Django REST Framework viewset that provides API endpoints for managing Child objects. It allows authenticated users to perform CRUD operations on their children, such as creating new child profiles, retrieving existing child profiles, updating child information, and deleting child profiles. The viewset uses the ChildSerializer for data serialization and deserialization, and it ensures that only authenticated users can access these endpoints. The get_queryset method filters the Child objects to return only those that belong to the currently authenticated user, ensuring that users can only manage their own children.
class ChildViewSet(viewsets.ModelViewSet):
    serializer_class = ChildSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get_queryset(self):
        return Child.objects.filter(user=self.request.user)

# The StoryViewSet is a Django REST Framework viewset that provides API endpoints for managing Story objects. It allows authenticated users to create new stories, retrieve their existing stories, and check the status of story generation. The viewset includes custom actions for checking the progress of story generation and for continuing the generation process if needed. It also handles the creation of story assets in the background and provides real-time updates on the progress of story generation through the status endpoint.
class StoryViewSet(viewsets.ModelViewSet):
    serializer_class = StorySerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]
    http_method_names = ["get", "post", "head", "options"]

    # The get_queryset method is responsible for retrieving the queryset of Story objects that are relevant to the current user. It filters the Story objects based on the user associated with the request. Additionally, if the action being performed is "list", it further filters the queryset to include only stories that have a status of "ready". This ensures that when a user requests a list of their stories, they only see those that are fully generated and ready for reading, while still allowing access to all their stories when performing other actions such as retrieving a specific story's details.
    def get_queryset(self):
        qs = Story.objects.filter(user=self.request.user)

        if self.action == "list":
            qs = qs.filter(status="ready")

        return qs

    # The create method is responsible for handling the creation of a new story based on the user's request. It validates the input data using the StoryCreateSerializer, retrieves the necessary related objects (Child, Genre, ArtStyle, and Behavior) from the database, and creates a new Story instance with the initial status set to "queued". After creating the story, it starts a background thread that runs the _run_story_pipeline function, which handles the entire process of generating the story content and assets. Finally, it returns a response containing the initial progress payload for the newly created story.
    def create(self, request, *args, **kwargs):
        serializer = StoryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            child = Child.objects.get(id=data["childId"], user=request.user)
            genre = Genre.objects.get(key=data["storyType"])
            art_style = ArtStyle.objects.get(key=data["artStyle"])
        except (Child.DoesNotExist, Genre.DoesNotExist, ArtStyle.DoesNotExist):
            return Response({"error": "Invalid story request"}, status=400)

        if (
            data["targetBehavior"] != "other"
            and not Behavior.objects.filter(key=data["targetBehavior"]).exists()
        ):
            return Response({"error": "Invalid behavior key"}, status=400)

        custom_behavior = (data.get("customBehavior") or "").strip()

        story = Story.objects.create(
            user=request.user,
            child=child,
            story_type=genre.key,
            art_style=art_style.key,
            target_behavior=data["targetBehavior"],
            custom_behavior=custom_behavior,
            status="queued",
            title="جاري إنشاء القصة...",
            pdf_status="pending",
            pdf_progress=0,
            pdf_error="",
        )

        background_thread = threading.Thread(
            target=_run_story_pipeline,
            args=(
                story.id,
                child.id,
                genre.key,
                art_style.key,
                data["targetBehavior"],
                custom_behavior,
            ),
            daemon=True,
        )

        background_thread.start()

        return Response(_story_progress_payload(story), status=201)

    # The status action is an API endpoint that allows clients to retrieve the current progress and status of a specific story. When a client makes a GET request to this endpoint with the story ID, the server fetches the story object and returns a payload containing information about the story's generation stage, progress, and other relevant details. This allows clients to provide real-time feedback to users about the status of their story generation process, such as whether it's still being generated, if the initial pages are ready for reading, or if there were any issues during generation.
    @action(detail=True, methods=["get"], url_path="status")
    def status(self, request, pk=None):
        story = self.get_object()
        return Response(_story_progress_payload(story))

    # The continue_generation action is an API endpoint that allows clients to trigger the continuation of the story generation process for a specific story. When a client makes a POST request to this endpoint with the story ID, the server checks if the story has raw JSON data and if its status is not "failed". If these conditions are met, it updates the PDF status to "pending" and resets the progress and error fields. Then, it starts a background thread that calls the _run_story_pipeline function with the necessary parameters to continue generating the story assets. This allows clients to manually trigger the continuation of story generation if needed, such as in cases where there was an interruption or if they want to refresh the generated content.
    @action(detail=True, methods=["post"], url_path="continue-generation")
    def continue_generation(self, request, pk=None):
        story = self.get_object()

        if story.raw_story_json and story.status != "failed":
            story.pdf_status = "pending"
            story.pdf_progress = 0
            story.pdf_error = ""
            story.save(update_fields=["pdf_status", "pdf_progress", "pdf_error"])

            background_thread = threading.Thread(
                target=_run_story_pipeline,
                args=(
                    story.id,
                    story.child.id,
                    story.story_type,
                    story.art_style,
                    story.target_behavior,
                    story.custom_behavior,
                ),
                daemon=True,
            )

            background_thread.start()

        return Response({"status": "started"})

    # The lazy_audio action is an API endpoint that allows clients to request the audio URL for a specific page of a story. When a client makes a GET request to this endpoint with the story ID and page number, the server checks if the audio for that page is already generated and cached. If it is, it returns the audio URL along with a flag indicating that it was cached. If the audio is not ready, it initiates the generation of the audio using the StoryOrchestrator's TTS service, updates the corresponding StoryPage entry in the database with the new audio URL and text hash, and then returns the audio URL once it's ready. This allows for on-demand generation of audio assets while providing feedback on whether the audio was served from cache or newly generated.
    @action(detail=True, methods=["get"], url_path=r"audio/(?P<page>[^/.]+)")
    def lazy_audio(self, request, pk=None, page=None):
        story = self.get_object()

        try:
            page_num = int(page)
            story_page = StoryPage.objects.get(
                story=story,
                page_number=page_num,
            )
        except Exception:
            return Response({"error": "Page not found"}, status=404)
        
        current_hash = _text_hash(story_page.narration_text)
        
        if (
            _page_audio_ready(story_page) and story_page.audio_text_hash == current_hash
        ):
            return Response( 
                {
                    "audio": story_page.audio_url,
                    "cached": True,
                }
            )

        orchestrator = StoryOrchestrator()
        audio_url = asyncio.run(
            orchestrator.tts.gen(story_page.narration_text)
        )

        story_page.audio_url = audio_url
        story_page.audio_text_hash = current_hash
        story_page.save(update_fields=["audio_url", "audio_text_hash"])

        if _page_audio_ready(story_page):
            return Response(
                {
                    "audio": audio_url,
                    "cached": False,
                }
            )

        return Response(
            {
                "error": "Audio generation failed",
                "audio": "",
                "cached": False,
            },
            status=500,
        )
    
    # The generate_pdf action allows users to initiate the generation of a PDF version of their story. When a user triggers this action, it first checks the current PDF status of the story. If the PDF is already ready and available, it returns the URL for downloading the PDF. If the PDF is still being generated, it returns the current progress and status. If the PDF generation has not started yet, it updates the story's PDF status to "generating" and starts a background thread to handle the PDF generation process. This allows users to request a PDF version of their story and receive updates on its progress without blocking the main application flow.
    @action(detail=True, methods=["post"], url_path="generate-pdf")
    def generate_pdf(self, request, pk=None):
        story = self.get_object()

        if story.pdf_status == "ready" and story.pdf_file:
            return Response(
                {
                    "status": "ready",
                    "progress": 100,
                    "ready": True,
                    "pdfUrl": story.pdf_file.url,
                    "error": "",
                }
            )

        if story.pdf_status == "generating":
            return Response(
                {
                    "status": "generating",
                    "progress": story.pdf_progress or 20,
                    "ready": False,
                    "pdfUrl": story.pdf_file.url if story.pdf_file else "",
                    "error": story.pdf_error,
                }
            )

        story.pdf_status = "generating"
        story.pdf_progress = 5
        story.pdf_error = ""
        story.save(update_fields=["pdf_status", "pdf_progress", "pdf_error"])

        threading.Thread(
            target=_generate_story_pdf_background,
            args=(story.id,),
            daemon=True,
        ).start()

        return Response(
            {
                "status": "generating",
                "progress": 5,
                "ready": False,
                "pdfUrl": "",
                "error": "",
            }
        )

    # The pdf_status action allows users to check the current status of their story's PDF generation. It returns information about whether the PDF is still being generated, if it's ready for download, and any errors that may have occurred during the generation process. This enables users to stay informed about the progress of their PDF and to know when they can access it.
    @action(detail=True, methods=["get"], url_path="pdf-status")
    def pdf_status(self, request, pk=None):
        story = self.get_object()

        return Response(
            {
                "status": story.pdf_status,
                "progress": story.pdf_progress,
                "ready": story.pdf_status == "ready" and bool(story.pdf_file),
                "pdfUrl": story.pdf_file.url if story.pdf_file else "",
                "error": story.pdf_error,
            }
        )
   
    
    # The download_pdf action allows users to download the generated PDF version of their story. It checks if the PDF is ready and available, and if so, it returns a FileResponse that prompts the user to download the PDF file. If the PDF is still being prepared or if there was an issue with generating the PDF, it returns an appropriate error response. This functionality provides users with a convenient way to access and share their stories in a widely compatible format.
    @action(detail=True, methods=["get"], url_path="download-pdf")
    def download_pdf(self, request, pk=None):
        story = self.get_object()

        if story.pdf_status != "ready" or not story.pdf_file:
            return Response(
                {"error": "PDF is still being prepared"},
                status=409,
            )

        filename = (story.title or f"story-{story.id}").replace('"', "")

        return FileResponse(
            story.pdf_file.open("rb"),
            content_type="application/pdf",
            as_attachment=True,
            filename=f"{filename}.pdf",
        )

# The create_behavior_task view function is responsible for creating a new behavior task entry when a user completes a behavior targeted in a story. It takes the request data, validates it using the BehaviorTaskCreateSerializer, and then checks if the specified child and story exist and belong to the authenticated user. If they do, it creates a new BehaviorTask entry with the provided behavior and response. This allows us to track the user's progress in completing tasks related to specific behaviors, which can be used for analytics and providing insights to the user about their development in those behaviors.
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_behavior_task(request):
    serializer = BehaviorTaskCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    # We attempt to retrieve the specified child and story from the database, ensuring that they belong to the authenticated user. If either the child or story does not exist, we return a 404 error response indicating that the child or story was not found. This validation step is crucial to ensure that users can only create behavior tasks for their own children and stories, maintaining data integrity and security within the application.
    try:
        child = Child.objects.get(id=data["childId"], user=request.user)
        story = Story.objects.get(id=data["storyId"], user=request.user)
    except (Child.DoesNotExist, Story.DoesNotExist):
        return Response({"error": "Child or story not found"}, status=404)

    behavior_value = data["behavior"]

    if behavior_value == "other" and story.custom_behavior:
        behavior_value = story.custom_behavior

    task = BehaviorTask.objects.create(
        user=request.user,
        child=child,
        story=story,
        behavior=behavior_value,
        response=data["response"],
    )

    return Response(BehaviorTaskSerializer(task).data, status=201)

# The create_reading_log view function is responsible for creating a new reading log entry when a user reads a story. It takes the request data, validates it using the ReadingLogCreateSerializer, and then checks if the specified child and story exist and belong to the authenticated user. If they do, it creates a new ReadingLog entry with the provided time spent and finished status. This allows us to track the user's reading activity, including how much time they spent reading and whether they completed the story, which can be used for analytics and providing insights to the user about their reading habits.
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_reading_log(request):
    serializer = ReadingLogCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    try:
        child = Child.objects.get(id=data["childId"], user=request.user)
        story = Story.objects.get(id=data["storyId"], user=request.user)
    except (Child.DoesNotExist, Story.DoesNotExist):
        return Response({"error": "Child or story not found"}, status=404)

    # We create a new ReadingLog entry to record the user's reading activity for a specific story and child. This log includes the time spent reading and whether the story was finished. By capturing this information, we can track the user's engagement with the stories, analyze their reading habits, and provide insights or recommendations based on their activity. This also allows us to calculate statistics such as reading streaks and to understand how users interact with the content over time.
    log = ReadingLog.objects.create(
        user=request.user,
        child=child,
        story=story,
        time_spent=data.get("timeSpent", 0),
        finished_at=timezone.now() if data.get("finished") else None,
    )

    return Response(ReadingLogSerializer(log).data, status=201)

# The stats view function retrieves various statistics related to the user's reading activity and behavior tasks. It calculates the total number of stories, the count of children, the number of stories read, and the number of tasks completed. It also prepares data for visualizations such as a weekly activity chart and a radar chart for behaviors. Additionally, it calculates the user's current reading streak based on their finished reading logs. Finally, it returns all these statistics in a JSON response that can be used by the frontend to display insights about the user's engagement and progress.
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def stats(request):
    user = request.user

    # We count the total number of stories that belong to the user and have a status of "ready". This gives us an indication of how many stories the user has successfully created and are available for reading. This metric can be used to track the user's content creation activity and to provide insights into their engagement with the story generation process.
    total_stories = Story.objects.filter(
        user=user,
        status="ready",
    ).count()

    children_count = Child.objects.filter(user=user).count()

    # We count the number of distinct stories that the user has finished reading by filtering the ReadingLog entries for the user where the finished_at field is not null. We then use values and distinct to get the unique story IDs and count them. This metric helps us understand how many different stories the user has engaged with and completed, which can provide insights into their reading habits and preferences.
    stories_read = (
        ReadingLog.objects.filter(
            user=user,
            finished_at__isnull=False,
        )
        .values("story_id")
        .distinct()
        .count()
    )

    # We count the total number of behavior tasks completed by the user. This metric helps us understand how actively the user is engaging with the behaviors targeted in the stories and can provide insights into their progress in developing those behaviors. It also allows us to track the effectiveness of the stories in encouraging users to complete tasks related to specific behaviors.
    tasks_completed = BehaviorTask.objects.filter(user=user).count()

    # We calculate the date range for the past week by getting today's date and subtracting 6 days to get the start date. This allows us to filter the reading logs to include only those that were started within the last 7 days, which is essential for analyzing the user's reading activity over the past week and preparing data for visualizations such as a weekly activity chart.
    today = timezone.localdate()
    start_date = today - timedelta(days=6)

    logs = ReadingLog.objects.filter(
        user=user,
        started_at__date__gte=start_date,
    )

    day_names = {
        5: "سبت",
        6: "أحد",
        0: "إثنين",
        1: "ثلاثاء",
        2: "أربعاء",
        3: "خميس",
        4: "جمعة",
    }

    daily_counts = {
        start_date + timedelta(days=i): 0
        for i in range(7)
    }

    # We iterate through the reading logs for the past week and count how many stories were started on each day. We use the started_at field of the ReadingLog model to determine the date when a story was started, and we increment the count for that date in the daily_counts dictionary. This allows us to track the user's reading activity over the past week and prepare data for visualizing their weekly reading habits.
    for log in logs:
        d = timezone.localtime(log.started_at).date()
        if d in daily_counts:
            daily_counts[d] += 1

    weekly_data = [
        {
            "day": day_names[d.weekday()],
            "stories": daily_counts[d],
        }
        for d in sorted(daily_counts.keys(), key=lambda x: x.weekday())
    ]

    behavior_counts = (
        BehaviorTask.objects.filter(user=user)
        .values("behavior")
        .annotate(count=Count("id"))
        .order_by("behavior")
    )

    behavior_labels = dict(Behavior.objects.values_list("key", "label"))

    # We prepare the data for the radar chart by iterating through the behavior counts and mapping each behavior key to its corresponding label using the behavior_labels dictionary. If a behavior key does not have a corresponding label, we use the key itself as the label. We also include the count of tasks completed for each behavior. This structured data allows us to visualize the distribution of completed tasks across different behaviors in a radar chart format.
    radar_data = [
        {
            "behavior": behavior_labels.get(row["behavior"], row["behavior"]),
            "key": row["behavior"],
            "count": row["count"],
        }
        for row in behavior_counts
    ]

    # We retrieve all the finished reading logs for the user and extract the unique finished dates. We then sort these dates in reverse order (most recent first) to facilitate the calculation of the current reading streak. This allows us to determine how many consecutive days the user has finished reading stories, which can be an important metric for tracking engagement and encouraging consistent reading habits.
    finished_dates = sorted(
        {
            timezone.localtime(log.finished_at).date()
            for log in ReadingLog.objects.filter(
                user=user,
                finished_at__isnull=False,
            )
        },
        reverse=True,
    )

    streak = 0
    cursor = today

    # We calculate the user's current reading streak by iterating through the sorted list of finished reading dates. Starting from today, we check if the user has finished a story on that date. If they have, we increment the streak count and move the cursor back by one day. If the user has finished a story on a date that is greater than the cursor (i.e., in the future), we ignore it and continue checking. If we encounter a date that is less than the cursor (i.e., a past date with no finished story), we break the loop, as this indicates that the streak has been interrupted. This logic allows us to accurately calculate how many consecutive days the user has finished reading stories, which can be used to motivate and encourage consistent reading habits.
    for d in finished_dates:
        if d == cursor:
            streak += 1
            cursor -= timedelta(days=1)
        elif d > cursor:
            continue
        else:
            break

    # Finally, we return a JSON response containing all the calculated statistics, including the total number of stories, the count of children, the number of stories read, the number of tasks completed, the current reading streak, and the data for both the radar chart and the weekly activity chart. This allows the frontend to display these statistics to the user in an informative and visually appealing way.
    return Response(
        {
            "totalStories": total_stories,
            "childrenCount": children_count,
            "storiesRead": stories_read,
            "tasksCompleted": tasks_completed,
            "streak": streak,
            "radarData": radar_data,
            "weeklyData": weekly_data,
        }
    )

# import nescessary libraries and load environment variables
@api_view(["GET"])
@permission_classes([AllowAny])
@renderer_classes([JSONRenderer])
def config(request):
    return Response(
        {
            "genres": STORY_TYPES,
            "styles": ART_STYLES,
            "behaviors": BEHAVIORS,
        }
    )

# The genres_list function is an API endpoint that returns a list of available story genres for story generation. It is decorated with @api_view(["GET"]) to specify that it handles GET requests, @permission_classes([AllowAny]) to allow access without authentication, and @renderer_classes([JSONRenderer]) to specify that the response should be rendered as JSON. When this endpoint is accessed, it simply returns a JSON response containing the predefined list of story genres defined in the STORY_TYPES variable. This allows clients to retrieve the available genres that can be used when creating a new story.
@api_view(["GET"])
@permission_classes([AllowAny])
@renderer_classes([JSONRenderer])
def genres_list(request):
    return Response(STORY_TYPES)

# The behaviors_list function is an API endpoint that returns a list of available behaviors for story generation. It is decorated with @api_view(["GET"]) to specify that it handles GET requests, @permission_classes([AllowAny]) to allow access without authentication, and @renderer_classes([JSONRenderer]) to specify that the response should be rendered as JSON. When this endpoint is accessed, it simply returns a JSON response containing the predefined list of behaviors defined in the BEHAVIORS variable. This allows clients to retrieve the available behaviors that can be used when creating a new story.
@api_view(["GET"])
@permission_classes([AllowAny])
@renderer_classes([JSONRenderer])
def behaviors_list(request):
    return Response(BEHAVIORS)

# The art_styles_list function is an API endpoint that returns a list of available art styles for story generation. It is decorated with @api_view(["GET"]) to specify that it handles GET requests, @permission_classes([AllowAny]) to allow access without authentication, and @renderer_classes([JSONRenderer]) to specify that the response should be rendered as JSON. When this endpoint is accessed, it simply returns a JSON response containing the predefined list of art styles defined in the ART_STYLES variable. This allows clients to retrieve the available art styles that can be used when creating a new story.
@api_view(["GET"])
@permission_classes([AllowAny])
@renderer_classes([JSONRenderer])
def art_styles_list(request):
    return Response(ART_STYLES)