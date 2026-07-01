# This module provides functions to generate story packages and initial assets using AI services. It includes a mock implementation for testing purposes when the OpenAI API key is not available, as well as integration with an orchestrator that manages the AI generation process. The functions are designed to be asynchronous to allow for efficient handling of AI requests and responses.
# Import necessary libraries for asynchronous programming, file handling, random number generation, and environment variable access. The module also defines helper functions for mocking story generation and asset creation when the OpenAI API key is not set, allowing for testing without making actual API calls.
import asyncio
import os
import random

# Load environment variables from a .env file to access the OpenAI API key and other configurations. This allows the module to determine whether to use mock data or make real API calls based on the presence of the API key.
from dotenv import load_dotenv

# Load environment variables to access the OpenAI API key and determine if mock data should be used for story generation and asset creation. If the API key is not set, the module will use predefined templates and random image URLs to simulate the AI-generated content for testing purposes.
load_dotenv()

# This function checks if the OpenAI API key is set in the environment variables. If the API key is not present, it returns True, indicating that the module should use mock data for story generation and asset creation. If the API key is available, it returns False, allowing the module to make real API calls to generate content using AI services.
def _use_mock() -> bool:
    return not os.getenv("OPENAI_API_KEY")

# A global variable to hold the instance of the StoryOrchestrator, which is responsible for managing the AI generation process. The orchestrator is initialized lazily when the _get_orchestrator function is called for the first time, ensuring that it is only created when needed and allowing for efficient resource management.
_orchestrator = None


# This function retrieves the instance of the StoryOrchestrator. If the orchestrator has not been initialized yet, it imports the StoryOrchestrator class from the ai_services.orchestrator module and creates an instance of it. The function then returns the orchestrator instance, allowing other functions in the module to use it for generating story packages and initial assets with AI services.
def _get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        from ai_services.orchestrator import StoryOrchestrator
        _orchestrator = StoryOrchestrator()
    return _orchestrator


# Define a list of scene templates that can be used to generate narration text for story scenes. These templates include placeholders for the child's name and the target behavior, allowing for dynamic generation of story content based on the specific child and behavior being targeted in the story.
_SCENE_TEMPLATES = [
    "في يوم جميل، استيقظ {name} وقرر أن يخوض مغامرة جديدة في حديقة المنزل.",
    "قابل {name} صديقاً صغيراً يحتاج إلى مساعدة، فتذكر أهمية {behavior}.",
    "واجه {name} تحدياً صعباً، لكنه لم يستسلم وتذكر أن {behavior} تجعل القلب قوياً.",
    "بمساعدة أصدقائه، تعلم {name} أن {behavior} شيء جميل نشاركه مع الآخرين.",
    "عاد {name} إلى البيت مبتسماً، وقد تعلم درساً لن ينساه عن {behavior}.",
]


# This function generates a mock image URL based on the story title and scene index. It uses the Picsum Photos service to create a unique image URL by hashing the combination of the story title and scene index to generate a seed for the random image. This allows for consistent mock images for the same story and scene, while still providing variety across different stories and scenes.
def _mock_image_url(story_title, idx):
    seed = abs(hash(f"{story_title}-{idx}")) % 100000
    return f"https://picsum.photos/seed/{seed}/800/800"


# This function generates a mock story package for testing purposes. It takes a child, behavior, and genre as input and creates a story with a title, cover prompt, and scenes based on predefined templates. The function populates the story data with the child's name, appearance, age group, image style, story type, target behavior
def _mock_story(child, behavior, genre):
    name = child.name
    behavior_label = behavior.label
    scenes = []
    for i, template in enumerate(_SCENE_TEMPLATES, start=1):
        scenes.append({
            "narration_text": template.format(name=name, behavior=behavior_label),
            "image_prompt": f"A child named {name} learning about {behavior_label}, scene {i}, {genre.label} style",
            "image": "",
            "audio": "",
        })
    return {
        "title": f"مغامرة {name} و{behavior_label}",
        "cover_prompt": f"Cover illustration: {name} in a {genre.label} adventure",
        "scenes": scenes,
        "cover_image": "",
    }

# This asynchronous function generates a story package using AI services. It takes a child, behavior, genre, and art style as input and returns a story package that includes the child's name, appearance, age group, image style, story type, target
async def generate_story_package_ai(child, behavior, genre, art_style):
    if _use_mock():
        await asyncio.sleep(random.uniform(0.8, 1.5))
        story = _mock_story(child, behavior, genre)
        story["child_name"] = child.name
        story["appearance"] = child.appearance_description
        story["age_group"] = child.age_group
        story["image_style"] = art_style.key
        story["story_type"] = genre.label
        story["target_behavior"] = behavior.label
        story["gender"] = child.gender
        story["cover_image"] = _mock_image_url(story["title"], 0)
        return story

    # If not using mock data, call the orchestrator's generate_story_package method with the appropriate parameters extracted from the child, behavior, genre, and art style objects. This will allow the orchestrator to handle the AI generation process and return a story package based on the provided inputs.
    return await _get_orchestrator().generate_story_package(
        child_name=child.name,
        gender=child.gender,
        appearance=child.appearance_description,
        age_group=child.age_group,
        story_type=genre.label,
        target_behavior=behavior.label,
        image_style=art_style.key,
    )

# This asynchronous function generates initial assets for a story using AI services. It takes story data, child, art style, an optional reference image, and the number of immediate assets to generate as input. The function populates the story data with default values based on the child and art style if they are not already set. If mock data is being used, it simulates the generation of image and audio assets for the scenes. Otherwise, it calls the orchestrator's generate_initial_assets method to perform the actual AI generation of assets based on the provided story data and reference image.
async def generate_initial_assets_ai(
    story_data,
    child,
    art_style,
    reference_image=None,       
    immediate_count: int = 3,
):
    story_data.setdefault("child_name", child.name)
    story_data.setdefault("appearance", child.appearance_description)
    story_data.setdefault("age_group", child.age_group)
    story_data.setdefault("image_style", art_style.key)
    story_data.setdefault("gender", child.gender)
    story_data.setdefault("story_type", story_data.get("story_type", ""))
    story_data.setdefault("target_behavior", story_data.get("target_behavior", ""))
    
    # If using mock data, simulate the generation of image and audio assets for the scenes by populating the story data with mock image URLs and audio file paths based on the story title and scene index. This allows for testing the asset generation process without making actual API calls to AI services.
    if _use_mock():
        await asyncio.sleep(random.uniform(0.5, 1.0))
        title = story_data.get("title", "story")
        scenes = story_data.get("scenes", [])
        for idx in range(min(immediate_count, len(scenes))):
            scenes[idx]["image"] = _mock_image_url(title, idx + 1)
            scenes[idx]["audio"] = f"/media/audio/mock_{idx+1}.mp3"
        return story_data
    
    # If not using mock data, call the orchestrator's generate_initial_assets method with the appropriate parameters extracted from the story data and reference image. This will allow the orchestrator to handle the AI generation process and return the story data with the generated assets based on the provided inputs.
    return await _get_orchestrator().generate_initial_assets(
        story_data=story_data,
        reference_image=reference_image,
        immediate_count=immediate_count,
    )
