# This module defines the FluxService class, which provides functionality for generating images using the Flux image generation model. The service composes detailed prompts based on the input parameters, including the scene description, child protagonist's characteristics, and the desired image style. It also handles reference images by normalizing them into a format suitable for the Flux model. The service sends requests to the Flux API and polls for the generated image until it's ready, returning the URL of the generated image. Additionally, it supports batch generation of images for multiple prompts concurrently while respecting a specified concurrency limit.
# import nescessary libraries and load environment variables
import asyncio
import base64
import mimetypes
import os
import hashlib
from pathlib import Path
import httpx
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the API key for the Flux service from environment variables
BFL_KEY = os.getenv("FLUX_API_KEY")

# Define paths for storing story images
BACKEND_DIR = Path(__file__).resolve().parents[1]
STORY_IMAGES_DIR = BACKEND_DIR / "media" / "story_images"

# Define base prompts and style mappings for the image generation
BASE_STYLE_PROMPT = """
Create a high-quality children's book illustration for the provided story scene.
The image should feel warm, safe, emotionally expressive, and easy for children to understand.
Use soft lighting, a clean composition, balanced colors, clear focal subjects, and expressive faces.
The illustration must not contain any text, letters, words, watermark, logo, signature, collage, split screen, distorted anatomy, or extra fingers.
""".strip()

# Define a prompt to incorporate Saudi cultural elements into the illustrations
SAUDI_CULTURAL_PROMPT = """
Incorporate subtle local Saudi cultural elements in every illustration.
Use culturally respectful Saudi-inspired visual details such as traditional clothing (e.g., long white Saudi thobe for {gender == boy}, long dress for {gender == girl}), family-friendly settings, warm hospitality, Arabic architectural patterns, desert landscapes, palm trees, local neighborhoods, recognizable Saudi-inspired landmarks.
These cultural details should support the story scene naturally without changing the main action or distracting from the child protagonist.
Keep all elements child-safe, respectful, and suitable for Arabic/Saudi children's stories.
""".strip()

# Define a prompt to ensure the child protagonist remains visually consistent across all scenes of the storybook
CHARACTER_LOCK = """
Create the main child protagonist as the same character across all scenes of one coherent storybook.

The child protagonist is {child_name}. The child is {gender}, in the age group {age_group}, with this appearance: {appearance}.

If a reference image is provided, use it as the PRIMARY identity source.
Carefully preserve the exact facial structure, skin tone, hairstyle, hair color, eye color, and overall identity from the reference image.
Do not reinterpret or redesign the character.

If no reference image is provided, use the textual appearance description as the PRIMARY identity source.
Strictly follow this description and keep it consistent across all scenes without introducing new features.

The character must remain visually identical across all images:
same face, same skin tone, same hairstyle, same age appearance, and same clothing style.

Only expressions, poses, and scene actions may change. Identity must not change.
Treat the character as a fixed identity token that must not change across scenes.
The final result must look like the same child appearing across multiple pages of one consistent illustrated storybook.
""".strip()

# Define a mapping of image styles to their corresponding prompt descriptions for the Flux image generation model
STYLE_MAP = {
    "storybook": (
        "Use a classic children's storybook illustration style with soft painterly rendering, "
        "a warm gentle color palette, subtle brush textures, and a slightly textured paper feel. "
        "The scene should look cozy, magical, emotionally expressive, and easy for children to understand."
    ),
    "cartoon": (
        "Use a colorful cartoon children's illustration style with clean bold outlines, smooth shading, "
        "bright balanced colors, playful shapes, and expressive facial emotions. "
        "The scene should feel fun, clear, energetic, and polished."
    ),
    "watercolor": (
        "Use a traditional watercolor children's illustration style with soft translucent watercolor layers, "
        "natural pigment diffusion, gentle color bleeding, visible watercolor paper texture, "
        "delicate hand-painted brush strokes, soft feathered edges, loose organic shapes, airy composition. "
        "The scene should feel dreamy, artistic, hand-painted, and child-friendly with subtle paint splashes. "
        "Avoid digital rendering, sharp outlines, vector appearance, and clean digital shading."
    ),
    "paper": (
        "Use a paper cut collage children's illustration style with layered paper shapes, "
        "visible paper textures, soft shadows between layers, simple color blocks, and a handmade tactile look. "
        "The scene should feel playful, artistic, clear, and suitable for a children's storybook."
    ),
    "pixel": (
        "Use a pixel art children's illustration style with a clean pixel grid, crisp square pixels, "
        "a limited retro color palette, simple readable shapes, and an 8-bit or 16-bit game-like look. "
        "The scene should remain child-friendly, clear, and visually consistent."
    ),
    "anime": (
        "Use a wholesome anime-style children's illustration with clean smooth line art, soft cel shading, "
        "large expressive eyes, gentle gradients, warm cinematic lighting, and emotionally expressive characters. "
        "The scene should feel magical, uplifting, polished, and child-friendly."
    ),
}

# Define the main service class for generating images using the Flux model
class FluxService:
    MODEL_URL = os.getenv("FLUX_MODEL_URL", "https://api.bfl.ai/v1/flux-2-max")

    # This method generates a stable seed based on the input parts to ensure consistent image generation for the same inputs
    def _stable_seed(self, *parts) -> int:
        seed_source = "-".join(str(part or "") for part in parts)
        digest = hashlib.sha256(seed_source.encode("utf-8")).hexdigest()
        return int(digest[:8], 16) % 100000
    
    # This method converts a local image file to a data URI format that can be used as an image prompt for the Flux model
    def _file_to_data_uri(self, file_path: str) -> str:
        if not file_path or not os.path.exists(file_path):
            raise FileNotFoundError(f"Reference image not found: {file_path}")
        
        # Guess the MIME type based on the file extension, default to "image/png" if it cannot be determined
        mime_type, _ = mimetypes.guess_type(file_path)

        # If MIME type cannot be determined, default to "image/png"
        if not mime_type:
            mime_type = "image/png"

        # Read the file in binary mode, encode it in base64, and format it as a data URI
        with open(file_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        
        # Return the data URI string that can be used as an image prompt for the Flux model
        return f"data:{mime_type};base64,{encoded}"
    
    # This method normalizes the reference image input, which can be a data URI, a URL, or a local file path. It returns a valid data URI or URL that can be used as an image prompt for the Flux model, or None if the input is invalid.
    def _normalize_reference_image(self, ref):
        if not ref:
            return None
        
        ref = str(ref).strip()

        if not ref:
            return None

        if ref.startswith("data:image/"):
            return ref

        if ref.startswith("http://") or ref.startswith("https://"):
            return ref

        if os.path.exists(ref):
            return self._file_to_data_uri(ref)

        return None
    
    # This method composes the final prompt for the Flux image generation model by combining the base style prompt, the Saudi cultural prompt, the specific style prompt based on the selected image style, the identity source instructions based on whether a reference image is provided, and the character lock instructions to ensure visual consistency of the child protagonist across all scenes. It also includes the specific scene prompt for the current image being generated.
    def _compose_prompt(
        self,
        scene_prompt: str,
        *,
        child_name="",
        appearance="",
        age_group="",
        image_style="",
        gender="",
        story_type="",
        target_behavior="",
        has_reference_image=False,
    ) -> str:
        style_key = (image_style or "").strip().lower()
        style_prompt = STYLE_MAP.get(style_key, STYLE_MAP.get("storybook", ""))

        if has_reference_image:
            identity_source = (
                "A reference image of the child is provided. Use that reference image as the primary identity source. "
                "Preserve the child's face, hairstyle, skin tone, eye color, age appearance, and overall identity. "
                "The textual description is secondary and should only support the reference image."
            )
        else:
            identity_source = (
                "No reference image is provided. Use the textual appearance description as the primary identity source. "
                "Strictly follow the described appearance and keep it consistent across all scenes."
            )

        character_prompt = CHARACTER_LOCK.format(
            child_name=(child_name or "the child protagonist").strip(),
            appearance=(appearance or "child-friendly appearance").strip(),
            age_group=(age_group or "unknown").strip(),
            gender=(gender or "unknown").strip(),
            story_type=(story_type or "unknown").strip(),
            target_behavior=(target_behavior or "unknown").strip(),
        )

        return "\n".join(
            [
                BASE_STYLE_PROMPT,
                SAUDI_CULTURAL_PROMPT,
                style_prompt,
                identity_source,
                character_prompt,
                (scene_prompt or "").strip(),
            ]
        ).strip()

    # This method builds the JSON payload for the Flux image generation API request based on the composed prompt, the normalized reference image (if any), the specified aspect ratio, and the seed for randomization. It returns a dictionary that can be sent as a JSON payload in the API request.
    def _build_payload(self, prompt: str, ref=None, aspect_ratio="1:1", seed=None):
        payload = {
            "prompt": (prompt or "").strip(),
            "aspect_ratio": aspect_ratio,
            "output_format": "jpeg",
            "prompt_upsampling": False,
        }

        if seed is not None:
            payload["seed"] = int(seed)

        if ref:
            payload["image_prompt"] = str(ref).split(",", 1)[-1]

        return payload
    
    # This method downloads the generated image from the provided URL and stores it locally in the designated story images directory. It uses a hash of the image URL to create a unique filename for caching purposes. If the image has already been downloaded and exists in the cache, it returns the cached image URL instead of downloading it again. If there is an error during download or storage, it logs the error and returns the original image URL.   
    async def _download_and_store_image(self, client: httpx.AsyncClient, image_url: str) -> str:
        image_url = (image_url or "").strip()

        if not image_url:
            return ""

        try:
            STORY_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

            image_hash = hashlib.sha256(
                image_url.encode("utf-8")
            ).hexdigest()

            filename = f"{image_hash}.jpeg"
            file_path = STORY_IMAGES_DIR / filename

            if file_path.exists() and file_path.stat().st_size > 0:
                return f"/media/story_images/{filename}"

            response = await client.get(
                image_url,
                timeout=60
            )

            if response.status_code != 200:
                print(
                    "IMAGE DOWNLOAD FAILED:",
                    response.status_code,
                    image_url
                )
                return image_url

            file_path.write_bytes(response.content)

            if (
                not file_path.exists()
                or file_path.stat().st_size == 0
            ):
                return image_url

            return f"/media/story_images/{filename}"

        except Exception as e:
            print("IMAGE STORE ERROR:", e)
            return image_url
    
    # This is the main method that generates an image based on the provided prompt, reference image, aspect ratio, and other parameters. It handles the entire process of normalizing the reference image, composing the final prompt, building the API request payload, sending the request to the Flux API, and polling for the result until the image is ready or a timeout occurs. It returns the URL of the generated image or an empty string if there was an error.
    async def gen(
        self,
        prompt,
        ref=None,
        aspect_ratio="1:1",
        *,
        child_name="",
        appearance="",
        age_group="",
        image_style="",
        gender="",
        story_type="",
        target_behavior="",
        seed=None,
    ):
        normalized_ref = self._normalize_reference_image(ref)
        has_reference_image = bool(normalized_ref)

        if seed is None:
            seed = self._stable_seed(
                child_name,
                appearance,
                age_group,
                gender,
                image_style,
            )

        if not BFL_KEY:
            fallback_seed = self._stable_seed(
                prompt,
                child_name,
                appearance,
                age_group,
                gender,
                image_style,
            )
            return f"https://picsum.photos/seed/{fallback_seed}/800/800"

        final_prompt = self._compose_prompt(
            prompt,
            child_name=child_name,
            appearance=appearance,
            age_group=age_group,
            image_style=image_style,
            gender=gender,
            story_type=story_type,
            target_behavior=target_behavior,
            has_reference_image=has_reference_image,
        )

        payload = self._build_payload(
            final_prompt,
            ref=normalized_ref,
            aspect_ratio=aspect_ratio,
            seed=seed,
        )

        # Send the image generation request to the Flux API and poll for the result until it's ready or a timeout occurs
        async with httpx.AsyncClient(timeout=180) as client:
            r = await client.post(
                self.MODEL_URL,
                headers={
                    "accept": "application/json",
                    "x-key": BFL_KEY,
                    "Content-Type": "application/json",
                },
                json=payload,
            )

            if r.status_code != 200:
                print("FLUX SUBMIT HTTP ERROR:", r.status_code, r.text)
                return ""

            data = r.json()
            polling_url = data.get("polling_url")

            if not polling_url:
                print("FLUX ERROR:", data)
                return ""

            for _ in range(90):
                await asyncio.sleep(1.0)

                poll = await client.get(
                    polling_url,
                    headers={
                        "accept": "application/json",
                        "x-key": BFL_KEY,
                    },
                )

                if poll.status_code != 200:
                    continue

                result = poll.json()
                status = str(result.get("status") or "").strip().lower()

                
                if status in {"ready", "completed"}:
                    output = result.get("result") or {}

                    remote_image_url = (
                        output.get("sample")
                        or output.get("image")
                        or output.get("url")
                        or ""
                    )

                    if not remote_image_url:
                        return ""

                    return await self._download_and_store_image(
                        client,
                        remote_image_url
                    )


                if status in {"error", "failed"}:
                    print("FLUX FAILED:", result)
                    return ""

            print("FLUX TIMEOUT")
            return ""

        
    # This method generates images for a batch of prompts concurrently while respecting a maximum concurrency limit. It uses asyncio to run multiple image generation tasks in parallel and collects the results in a list. If any individual generation fails, it logs the error and returns an empty string for that prompt.
    async def batch(
        self,
        prompts,
        ref=None,
        aspect_ratio="1:1",
        *,
        child_name="",
        appearance="",
        age_group="",
        image_style="",
        gender="",
        story_type="",
        target_behavior="",
        seed=None,
        max_concurrent=8,
    ):
        if not prompts:
            return []

        if seed is None:
            seed = self._stable_seed(
                child_name,
                appearance,
                age_group,
                gender,
                image_style,
            )

        sem = asyncio.Semaphore(max_concurrent)
        
        # Define an inner function to run a single image generation task while respecting the concurrency limit
        async def run_one(prompt):
            async with sem:
                try:
                    return await self.gen(
                        prompt,
                        ref=ref,
                        aspect_ratio=aspect_ratio,
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
                    print("FLUX GEN ERROR:", e)
                    return ""
        # Create a list of tasks for each prompt and run them concurrently using asyncio.gather to collect the results
        tasks = [run_one(prompt) for prompt in prompts]
        return await asyncio.gather(*tasks)