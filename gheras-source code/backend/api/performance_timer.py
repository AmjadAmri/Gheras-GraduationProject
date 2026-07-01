"""
api/performance_timer.py

Performance instrumentation for the real Gheras story-generation pipeline.

Purpose:
- The timer runs inside the same backend pipeline that is triggered when the
  user clicks Generate in the frontend.
- It measures the actual wall-clock response time of:
    1) LLM story generation
    2) Image generation for all story scenes + cover image
    3) TTS generation for all story scenes
    4) First viewable readiness time
    5) End-to-end full asset readiness time
- It prints the final report in the backend terminal after generation finishes.

How to use in api/views.py:
    from api.performance_timer import (
        PipelinePerformanceTimer,
        generate_initial_assets_with_timing_and_live_db_progress,
        generate_remaining_assets_with_timing,
    )

Then create a timer at the beginning of _run_story_pipeline and wrap the
existing generation calls as shown in the integration snippet below.
"""

# import necessary modules and classes for the performance timer and AI orchestrator
from __future__ import annotations

import asyncio
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from asgiref.sync import sync_to_async

from api.models import StoryPage
from ai_services.orchestrator import StoryOrchestrator

import hashlib

# Define a helper function to generate a hash from a given text input. This function uses the MD5 hashing algorithm to create a unique identifier for the input text, which can be useful for tracking and logging purposes in the performance timer. The input text is stripped of leading and trailing whitespace, encoded in UTF-8 format, and then hashed to produce a consistent output for the same input text.
def _text_hash(text: str) -> str:
    return hashlib.md5((text or "").strip().encode("utf-8")).hexdigest()

# Define a function to get an instance of the StoryOrchestrator. This function is decorated with @sync_to_async, which allows it to be called in an asynchronous context while still executing synchronously. The function simply returns a new instance of the StoryOrchestrator class, which is responsible for handling the story generation process using AI services.
@dataclass
class TimedEvent:
    name: str
    started_at: str
    ended_at: str
    duration_seconds: float
    meta: Dict[str, Any] = field(default_factory=dict)

# Define an asynchronous function to retrieve the StoryOrchestrator instance. This function is decorated with @sync_to_async, allowing it to be called in an asynchronous context while still executing synchronously. It simply returns a new instance of the StoryOrchestrator class, which is responsible for managing the AI generation process for stories.
class PipelinePerformanceTimer:
    """
    Collects timing data for one real story generation request.

    Important distinction:
    - wall-clock duration = actual elapsed time experienced by the user.
    - accumulated service time = sum of individual API/task durations. This can
      be larger than wall-clock time because image/TTS tasks run in parallel.
    """
    
    # Initialize the PipelinePerformanceTimer with various attributes to track the performance of the story generation pipeline. The constructor takes parameters such as story_id, child_name, age_group, image_style, story_type, and target_behavior to provide context for the performance data being collected. It also initializes timing attributes like started_perf and started_at to record when the timer was started, as well as lists to hold events related to LLM generation, image generation, and TTS generation. The constructor prints a header with the initial information about the story generation request for easy reference in the logs.
    def __init__(
        self,
        *,
        story_id: int,
        child_name: str = "",
        age_group: str = "",
        image_style: str = "",
        story_type: str = "",
        target_behavior: str = "",
    ):
        self.story_id = story_id
        self.child_name = child_name
        self.age_group = age_group
        self.image_style = image_style
        self.story_type = story_type
        self.target_behavior = target_behavior

        self.started_perf = time.perf_counter()
        self.started_at = datetime.now()
        self.ended_perf: Optional[float] = None
        self.ended_at: Optional[datetime] = None

        self.total_scenes = 0
        self.initial_pages_target = 0

        self.events: List[TimedEvent] = []
        self.llm_seconds: float = 0.0

        self.image_events: List[TimedEvent] = []
        self.tts_events: List[TimedEvent] = []

        self.first_viewable_ready_perf: Optional[float] = None
        self.first_viewable_ready_at: Optional[datetime] = None

        self.status = "running"
        self.error_message = ""

        self._print_header()

    # Helper method to get the current timestamp as a formatted string. This method is used to provide consistent timestamps in the log messages for the performance timer, allowing for easy tracking of when each stage of the story generation process starts and ends. The timestamp is formatted to include the date and time down to milliseconds for precise logging.
    def _now_str(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

# Helper method to calculate the elapsed time since the timer was started. This method uses the perf_counter function to get a high-resolution timer value and calculates the difference from the time when the timer was initialized. The elapsed time is returned in seconds as a floating-point number, which can be used for logging and performance analysis throughout the story generation pipeline.
    def _elapsed(self) -> float:
        return time.perf_counter() - self.started_perf
     
    # Helper method to print a header with the initial information about the story generation request. This method is called during the initialization of the PipelinePerformanceTimer and provides a clear and formatted output in the logs that includes details such as the story ID, child name, age group, image style, story type, target behavior, and the timestamp when the timer was started. This header serves as a reference point for all subsequent log messages related to this specific story generation request.
    def _print_header(self) -> None:
        print("\n" + "=" * 88, flush=True)
        print("GHERAS STORY GENERATION PERFORMANCE TIMER STARTED", flush=True)
        print("=" * 88, flush=True)
        print(f"Story ID        : {self.story_id}", flush=True)
        print(f"Child           : {self.child_name or '-'}", flush=True)
        print(f"Age group       : {self.age_group or '-'}", flush=True)
        print(f"Image style     : {self.image_style or '-'}", flush=True)
        print(f"Story type      : {self.story_type or '-'}", flush=True)
        print(f"Target behavior : {self.target_behavior or '-'}", flush=True)
        print(f"Start timestamp : {self.started_at.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}", flush=True)
        print("=" * 88 + "\n", flush=True)

    # This private method sends a chat message to the LLM and expects a JSON response. It constructs the system prompt and user prompt, then calls the orchestrator's chat method with the appropriate parameters. The response from the LLM is expected to be a JSON object, which is parsed and returned as a Python dictionary. If the LLM returns an empty response, an exception is raised to indicate that the story generation failed.
    def configure_story_counts(self, *, total_scenes: int, initial_pages_target: int) -> None:
        self.total_scenes = total_scenes
        self.initial_pages_target = initial_pages_target
        print(
            f"[PERF][{self._now_str()}] Story structure ready | "
            f"total_scenes={total_scenes}, initial_pages_target={initial_pages_target}",
            flush=True,
        )
    
    # This method logs a performance stage with a message and optional metadata. It calculates the elapsed time since the timer was started and includes it in the log output, along with any additional metadata provided as keyword arguments. The log message is formatted to include the current timestamp, elapsed time, and any relevant information about the stage being logged, making it easier to track the progress and performance of different stages in the story generation pipeline.
    def log_stage(self, message: str, **meta: Any) -> None:
        extra = ""
        if meta:
            extra = " | " + ", ".join(f"{k}={v}" for k, v in meta.items())
        print(f"[PERF][{self._now_str()}][+{self._elapsed():.3f}s] {message}{extra}", flush=True)
    
    # This context manager is used to measure the performance of a synchronous block of code. It records the start time and logs the beginning of the stage with the provided name and metadata. After the block of code is executed, it records the end time, calculates the duration, and logs the completion of the stage along with the duration in seconds. The performance data is stored in a TimedEvent object, which is added to the list of events for later reporting. If the stage being measured is "LLM story generation", it also updates the llm_seconds attribute with the duration.
    @contextmanager
    def measure_sync(self, name: str, **meta: Any):
        start_perf = time.perf_counter()
        start_str = self._now_str()
        self.log_stage(f"START {name}", **meta)
        try:
            yield
        finally:
            end_perf = time.perf_counter()
            end_str = self._now_str()
            duration = end_perf - start_perf
            event = TimedEvent(
                name=name,
                started_at=start_str,
                ended_at=end_str,
                duration_seconds=duration,
                meta=meta,
            )
            self.events.append(event)
            if name == "LLM story generation":
                self.llm_seconds = duration
            self.log_stage(f"END {name}", duration_seconds=f"{duration:.3f}", **meta)
    
    # This asynchronous method is used to measure the performance of an asynchronous operation, such as image generation or TTS generation. It takes an awaitable (coroutine) as input, along with optional parameters for scene number and kind (e.g., "cover" or "scene"). The method records the start time, logs the beginning of the stage, and then awaits the completion of the provided awaitable. After the operation completes, it records the end time, calculates the duration, and logs the completion of the stage along with the duration in seconds. The performance data is stored in a TimedEvent object, which is added to either the image_events or tts_events list based on the kind of operation being measured.
    async def measure_image(self, awaitable, *, scene_number: Optional[int] = None, kind: str = "scene"):
        label = "cover image" if kind == "cover" else f"scene {scene_number} image"
        start_perf = time.perf_counter()
        start_str = self._now_str()
        self.log_stage(f"START image generation: {label}")
        try:
            return await awaitable
        finally:
            end_perf = time.perf_counter()
            end_str = self._now_str()
            duration = end_perf - start_perf
            event = TimedEvent(
                name=f"image:{label}",
                started_at=start_str,
                ended_at=end_str,
                duration_seconds=duration,
                meta={"kind": kind, "scene_number": scene_number},
            )
            self.image_events.append(event)
            self.log_stage(
                f"END image generation: {label}",
                duration_seconds=f"{duration:.3f}",
            )
    
    # This asynchronous method is used to measure the performance of a TTS generation operation for a specific scene. It takes an awaitable (coroutine) as input, along with the scene number. The method records the start time, logs the beginning of the TTS generation for the specified scene, and then awaits the completion of the provided awaitable. After the operation completes, it records the end time, calculates the duration, and logs the completion of the TTS generation along with the duration in seconds. The performance data is stored in a TimedEvent object, which is added to the tts_events list for later reporting.
    async def measure_tts(self, awaitable, *, scene_number: int):
        start_perf = time.perf_counter()
        start_str = self._now_str()
        self.log_stage(f"START TTS generation: scene {scene_number}")
        try:
            return await awaitable
        finally:
            end_perf = time.perf_counter()
            end_str = self._now_str()
            duration = end_perf - start_perf
            event = TimedEvent(
                name=f"tts:scene {scene_number}",
                started_at=start_str,
                ended_at=end_str,
                duration_seconds=duration,
                meta={"scene_number": scene_number},
            )
            self.tts_events.append(event)
            self.log_stage(
                f"END TTS generation: scene {scene_number}",
                duration_seconds=f"{duration:.3f}",
            )
    
    # This method is used to mark the point in time when the first viewable story content is ready for the user. It checks if the first_viewable_ready_perf attribute is already set, and if not, it records the current time as the first viewable ready time. It then logs this stage with a message indicating that the first viewable story is ready, along with metadata such as the initial pages target and the elapsed time since the timer was started. This information can be useful for understanding how quickly the user can start interacting with the generated story content.
    def mark_first_viewable_ready(self) -> None:
        if self.first_viewable_ready_perf is not None:
            return
        self.first_viewable_ready_perf = time.perf_counter()
        self.first_viewable_ready_at = datetime.now()
        self.log_stage(
            "FIRST VIEWABLE STORY READY",
            initial_pages_target=self.initial_pages_target,
            elapsed_seconds=f"{self.first_viewable_duration_seconds():.3f}",
        )
    
    # This method calculates the duration in seconds from when the timer was started to when the first viewable story content is ready. It checks if the first_viewable_ready_perf attribute is set, and if not, it returns 0.0 to indicate that the first viewable content is not yet ready. If it is set, it calculates the difference between the first_viewable_ready_perf and the started_perf to determine how long it took for the first viewable content to be ready, and returns this duration in seconds as a floating-point number.
    def first_viewable_duration_seconds(self) -> float:
        if self.first_viewable_ready_perf is None:
            return 0.0
        return self.first_viewable_ready_perf - self.started_perf
    
    # This private method calculates the wall-clock duration for a list of timed events. It takes a list of TimedEvent objects as input and determines the earliest start time and the latest end time among the events. The method then calculates the total elapsed time between these two timestamps, which represents the wall-clock duration for the events. If there are no events in the list, it returns 0.0 to indicate that there is no duration to calculate.
    def _wall_clock_range(self, events: List[TimedEvent]) -> float:
        if not events:
            return 0.0
        starts = []
        ends = []
        fmt = "%Y-%m-%d %H:%M:%S.%f"
        for event in events:
            starts.append(datetime.strptime(event.started_at, fmt))
            ends.append(datetime.strptime(event.ended_at, fmt))
        return (max(ends) - min(starts)).total_seconds()
    
    # This private method calculates the accumulated service time for a list of timed events. It takes a list of TimedEvent objects as input and sums up the duration_seconds attribute of each event to get the total accumulated service time. This represents the total time spent on the individual tasks or API calls, regardless of whether they were executed in parallel or sequentially. The method returns the accumulated service time in seconds as a floating-point number.
    def _sum_duration(self, events: List[TimedEvent]) -> float:
        return sum(event.duration_seconds for event in events)

    # This method is called to finish the performance timer and print the final report. It takes optional parameters for status and error_message to indicate the outcome of the story generation process. The method updates the status and error message attributes, records the end time using perf_counter and datetime, and then calls the print_report method to output a detailed performance report in the backend terminal. The report includes information about the story generation request, timing data for each stage, and a breakdown of image and TTS events.
    def finish(self, *, status: str = "completed", error_message: str = "") -> None:
        self.status = status
        self.error_message = error_message or ""
        self.ended_perf = time.perf_counter()
        self.ended_at = datetime.now()
        self.print_report()

    # This method prints a detailed performance report for the story generation process. It calculates the end-to-end duration, wall-clock durations for image and TTS events, and accumulated service times. The report includes information about the story ID, status, error message (if any), age group, image style, total scenes, initial pages target, start and end timestamps, and timing data for each stage of the pipeline. It also provides a breakdown of individual image and TTS events with their respective durations and timestamps. The report is formatted for easy reading in the backend terminal.
    def print_report(self) -> None:
        end_to_end_seconds = (
            (self.ended_perf or time.perf_counter()) - self.started_perf
        )

        image_wall = self._wall_clock_range(self.image_events)
        image_sum = self._sum_duration(self.image_events)
        tts_wall = self._wall_clock_range(self.tts_events)
        tts_sum = self._sum_duration(self.tts_events)

        scene_image_events = [e for e in self.image_events if e.meta.get("kind") == "scene"]
        cover_image_events = [e for e in self.image_events if e.meta.get("kind") == "cover"]

        print("\n" + "=" * 88, flush=True)
        print("GHERAS STORY GENERATION PERFORMANCE REPORT", flush=True)
        print("=" * 88, flush=True)
        print(f"Story ID                 : {self.story_id}", flush=True)
        print(f"Status                   : {self.status}", flush=True)
        if self.error_message:
            print(f"Error                    : {self.error_message}", flush=True)
        print(f"Age group                : {self.age_group or '-'}", flush=True)
        print(f"Image style              : {self.image_style or '-'}", flush=True)
        print(f"Total scenes             : {self.total_scenes or len(self.tts_events)}", flush=True)
        print(f"Initial pages target     : {self.initial_pages_target or '-'}", flush=True)
        print(f"Started at               : {self.started_at.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}", flush=True)
        if self.ended_at:
            print(f"Ended at                 : {self.ended_at.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}", flush=True)
        print("-" * 88, flush=True)
        print(f"1. LLM response time                 : {self.llm_seconds:.3f}s", flush=True)
        print(
            f"2. Image generation time wall-clock  : {image_wall:.3f}s "
            f"({len(scene_image_events)} scene images + {len(cover_image_events)} cover image)",
            flush=True,
        )
        print(
            f"   Image accumulated service time     : {image_sum:.3f}s",
            flush=True,
        )
        print(
            f"3. TTS generation time wall-clock    : {tts_wall:.3f}s "
            f"({len(self.tts_events)} scene audios)",
            flush=True,
        )
        print(
            f"   TTS accumulated service time       : {tts_sum:.3f}s",
            flush=True,
        )
        print(
            f"4. First viewable ready time          : {self.first_viewable_duration_seconds():.3f}s",
            flush=True,
        )
        print(f"5. End-to-end full pipeline time      : {end_to_end_seconds:.3f}s", flush=True)
        print("-" * 88, flush=True)
        print("Detailed image events:", flush=True)
        if self.image_events:
            for event in self.image_events:
                print(
                    f"  - {event.name:<22} {event.duration_seconds:>8.3f}s "
                    f"[{event.started_at} -> {event.ended_at}]",
                    flush=True,
                )
        else:
            print("  - No image events recorded", flush=True)

        print("Detailed TTS events:", flush=True)
        if self.tts_events:
            for event in self.tts_events:
                print(
                    f"  - {event.name:<22} {event.duration_seconds:>8.3f}s "
                    f"[{event.started_at} -> {event.ended_at}]",
                    flush=True,
                )
        else:
            print("  - No TTS events recorded", flush=True)

        print("=" * 88 + "\n", flush=True)

# This asynchronous function generates the initial assets (images and TTS) for the story scenes while updating the database with live progress. It takes the story data, story ID, performance timer, reference image, and the number of immediate pages to generate as parameters. The function uses the StoryOrchestrator to generate images and TTS for each scene in parallel, while also measuring the performance of each generation task using the provided timer. The generated assets are saved back to the database immediately after they are created, allowing for a responsive user experience in the frontend.
async def generate_initial_assets_with_timing_and_live_db_progress(
    *,
    story_data: dict,
    story_id: int,
    timer: PipelinePerformanceTimer,
    reference_image=None,
    immediate_count: int = 3,
):
    """
    Generates the first pages in parallel and updates the DB immediately.

    This replaces generate_initial_assets_with_live_db_progress when timing is
    needed. It preserves the live progress behavior for pagesWithImages and
    pagesWithAudio while recording image/TTS durations separately.
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

    async def generate_page(idx: int):
        scene = scenes[idx]
        page_number = idx + 1

        async def generate_image():
            try:
                image_url = await timer.measure_image(
                    orchestrator.flux.gen(
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
                    ),
                    scene_number=page_number,
                    kind="scene",
                )
            except Exception as e:
                print("INITIAL SCENE IMAGE FAILED:", e, flush=True)
                image_url = scene.get("image") or ""

            scene["image"] = image_url or scene.get("image") or ""
            await update_page_field(page_number, illustration_url=scene["image"])

        async def generate_audio():
            try:
                audio_url = await timer.measure_tts(
                    orchestrator.tts.gen(scene.get("narration_text", "")),
                    scene_number=page_number,
                )
            except Exception as e:
                print("INITIAL SCENE AUDIO FAILED:", e, flush=True)
                audio_url = scene.get("audio") or ""

            scene["audio"] = audio_url or scene.get("audio") or ""
            await update_page_field(page_number, audio_url=scene["audio"], audio_text_hash=_text_hash(scene.get("narration_text", "")))

        await asyncio.gather(generate_image(), generate_audio())

    tasks = [generate_page(idx) for idx in range(immediate_count)]

    if tasks:
        await asyncio.gather(*tasks)

    return story_data

# This asynchronous function generates the remaining assets (images and TTS) for the story scenes, as well as the cover image, while keeping the performance timing visible. It takes the story data, performance timer, reference image, and the starting index for generation as parameters. The function uses the StoryOrchestrator to generate images and TTS for each remaining scene in parallel, while also measuring the performance of each generation task using the provided timer. The generated assets are stored in the story_data dictionary, allowing for further processing or saving to the database after generation is complete.
async def generate_remaining_assets_with_timing(
    *,
    story_data: dict,
    timer: PipelinePerformanceTimer,
    reference_image=None,
    start_index: int = 3,
):
    """
    Generates remaining scene images/TTS plus cover image with timing.

    This mirrors StoryOrchestrator.generate_remaining_assets, but keeps timing
    visible for:
    - all remaining scene images
    - all remaining scene TTS files
    - cover image
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

    sem = asyncio.Semaphore(3)

    async def run_scene(idx: int):
        scene = scenes[idx]
        page_number = idx + 1

        async with sem:
            async def gen_image():
                try:
                    return await timer.measure_image(
                        orchestrator.flux.gen(
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
                        ),
                        scene_number=page_number,
                        kind="scene",
                    )
                except Exception as e:
                    print("REMAINING SCENE IMAGE FAILED:", e, flush=True)
                    return scene.get("image") or ""

            async def gen_audio():
                try:
                    return await timer.measure_tts(
                        orchestrator.tts.gen(scene.get("narration_text", "")),
                        scene_number=page_number,
                    )
                except Exception as e:
                    print("REMAINING SCENE AUDIO FAILED:", e, flush=True)
                    return scene.get("audio") or ""

            image, audio = await asyncio.gather(gen_image(), gen_audio())
            scene["image"] = image or scene.get("image") or ""
            scene["audio"] = audio or scene.get("audio") or ""
            return scene

    async def run_cover():
        cover_prompt = (story_data.get("cover_prompt") or "").strip()

        if not cover_prompt:
            return story_data.get("cover_image") or ""

        try:
            return await timer.measure_image(
                orchestrator.flux.gen(
                    prompt=cover_prompt,
                    ref=reference_image,
                    aspect_ratio="3:4",
                    child_name=child_name,
                    appearance=appearance,
                    age_group=age_group,
                    gender=gender,
                    story_type=story_type,
                    target_behavior=target_behavior,
                    image_style=image_style,
                    seed=seed,
                ),
                scene_number=None,
                kind="cover",
            )
        except Exception as e:
            print("COVER GENERATION FAILED:", e, flush=True)
            return story_data.get("cover_image") or ""

    tasks = [run_scene(idx) for idx in range(start_index, len(scenes))]
    tasks.append(run_cover())

    if tasks:
        results = await asyncio.gather(*tasks)
        story_data["cover_image"] = results[-1] or story_data.get("cover_image") or ""

    return story_data
