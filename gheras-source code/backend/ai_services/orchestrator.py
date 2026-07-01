# This code defines a StoryOrchestrator class that serves as the main coordinator for generating children's stories in Arabic. It interacts with three services: LLMService for generating story text, FluxService for generating images based on prompts, and TTSService for generating audio narration. The orchestrator builds prompts for the LLM based on user input, generates the initial story package, and then creates the necessary assets (images and audio) for each scene in the story. It also includes methods for normalizing the story structure and ensuring that the generated text is suitable for children with appropriate diacritics.
# import necessary modules and services for the StoryOrchestrator class, including asyncio for asynchronous programming, and the LLMService, FluxService, and TTSService for handling language generation, image generation, and text-to-speech conversion respectively.
import asyncio
from .llm_service import LLMService
from .flux_image_service import FluxService
from .tts_service import TTSService

# Define the StoryOrchestrator class that serves as the main coordinator for generating children's stories in Arabic, including methods for building prompts, generating story packages, and creating assets for each scene.
class StoryOrchestrator:
    # Initialize the StoryOrchestrator by creating instances of the LLMService, FluxService, and TTSService that will be used for generating story text, images, and audio respectively.
    def __init__(self):
        self.llm = LLMService()
        self.flux = FluxService()
        self.tts = TTSService()

    # This private method returns the maximum token limit for the LLM response based on the specified age group. It uses a dictionary to map age groups to their corresponding token limits, with a default value of 2800 tokens if the age group is not found in the dictionary.
    def _max_tokens(self, age_group):
        return {
            "4-5": 1500,
            "6-7": 2800,
            "8-9": 4500,
        }.get(age_group, 2800)
    
    # This private method returns the number of scenes that should be generated for a story based on the specified age group. It uses a dictionary to map age groups to their corresponding scene counts, with a default value of 5 scenes if the age group is not found in the dictionary.
    def _scene_count(self, age_group):
        return {
            "4-5": 3,
            "6-7": 5,
            "8-9": 7,
        }.get(age_group, 5)
    
    # This private method calculates the ratio of diacritic characters to Arabic letters in a given text. It uses regular expressions to find all Arabic letters and diacritic characters, and then computes the ratio. If there are no Arabic letters, it returns 0.0 to avoid division by zero.
    def _character_seed(
        self,
        child_name="",
        appearance="",
        age_group="",
        gender="",
        image_style="",
    ):
        seed_source = f"{child_name}-{appearance}-{age_group}-{gender}-{image_style}"
        return abs(hash(seed_source)) % 100000
    
    # This private method calculates the ratio of diacritic characters to Arabic letters in a given text. It uses regular expressions to find all Arabic letters and diacritic characters, and then computes the ratio. If there are no Arabic letters, it returns 0.0 to avoid division by zero.
    def _safe_normalize_story(
        self,
        original_story: dict,
        normalized_story: dict,
    ) -> dict:
        if not isinstance(normalized_story, dict):
            return original_story

        original_scenes = original_story.get("scenes") or []
        normalized_scenes = normalized_story.get("scenes") or []

        if not normalized_scenes or len(normalized_scenes) != len(original_scenes):
            return original_story

        for i, scene in enumerate(normalized_scenes):
            if not scene.get("narration_text"):
                scene["narration_text"] = original_scenes[i].get(
                    "narration_text",
                    "",
                )

            if not scene.get("image_prompt"):
                scene["image_prompt"] = original_scenes[i].get(
                    "image_prompt",
                    "",
                )

        if not normalized_story.get("title"):
            normalized_story["title"] = original_story.get("title", "")

        if not normalized_story.get("cover_prompt"):
            normalized_story["cover_prompt"] = original_story.get(
                "cover_prompt",
                "",
            )

        return normalized_story

    # This private method calculates the ratio of diacritic characters to Arabic letters in a given text. It uses regular expressions to find all Arabic letters and diacritic characters, and then computes the ratio. If there are no Arabic letters, it returns 0.0 to avoid division by zero.
    def _style_template(self, image_style: str) -> str:
        style = (image_style or "").strip().lower()

        templates = {
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
                "Use a watercolor children's book illustration style with soft translucent brush strokes, "
                "gentle pigment blending, visible paper grain, pastel colors, and calm natural lighting. "
                "The scene should feel dreamy, warm, handcrafted, and child-friendly."
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

        return templates.get(
            style,
            "Beautiful children's story illustration, warm family-friendly style, clear main character, strong consistency.",
        )
    
    # This private method checks if a given story dictionary needs more diacritics based on the ratio of diacritic characters to Arabic letters in the title and narration texts. It combines the title and narration texts into a single string and calculates the diacritic ratio. If the ratio is below a specified minimum threshold (default is 0.35), it returns True, indicating that the story needs more diacritics; otherwise, it returns False.
    def build_prompt(
        self,
        child_name,
        gender,
        appearance,
        age_group,
        story_type,
        target_behavior,
        image_style,
    ):
        scenes = self._scene_count(age_group)
        style_template = self._style_template(image_style)

        return f"""أنت كاتب قصص أطفال عربي محترف.

أنشئ قصة أطفال عربية مناسبة للعمر المحدد. يجب أن يكون النص:
- صحيحًا لغويًا، بسيطًا، واضحًا، ومترابطًا
- مناسبًا للأطفال من حيث الأسلوب والمفردات
- بطله الأساسي هو الطفل المذكور
- السلوك المستهدف يظهر بشكل طبيعي داخل الأحداث
- استخدم كلمات عربية صحيحة ومفهومة فقط
- ممنوع استخدام كلمات غير موجودة في العربية أو كلمات مشوهة أو غير مفهومة

مراجعة النص قبل الإخراج:
- بعد كتابة كل narration_text، راجعه لغويًا قبل إخراج JSON النهائي
- تأكد أن كل كلمة عربية صحيحة وواضحة ومناسبة لعمر الطفل
- إذا كانت أي كلمة غير واضحة أو غير دقيقة، استبدلها داخل نفس النص بكلمة عربية بسيطة وصحيحة قبل الإخراج
- لا تُخرج أي كلمة مشوهة أو غير مفهومة
- النص الذي تكتبه في narration_text هو النص النهائي نفسه الذي سيُعرض للطفل ويُستخدم للصوت TTS، لذلك يجب أن يكون واضحًا وقابلًا للنطق

التشكيل (الحركات):
- اكتب العنوان (title) وكل narration_text باللغة العربية مع تشكيل واضح ومناسب للأطفال
- يجب أن يكون narration_text مُشَكَّلًا بشكل يساعد الطفل على القراءة الصحيحة
- ركّز على وضوح النطق أكثر من الإعراب الكامل

قواعد التشكيل:
- استخدم الحركات الأساسية: فتحة، ضمة، كسرة، سكون، وشدة
- يمكنك استخدام التنوين فقط إذا كنت متأكدًا من صحته
- راعِ الدقة النحوية قدر الإمكان، خصوصًا في الكلمات الشائعة والبسيطة
- لا تضف تشكيلًا إذا لم تكن متأكدًا من صحته
- لا تكتب تشكيلًا عشوائيًا أو غير دقيق
- تجنّب المبالغة في التشكيل إذا كانت ستؤدي إلى أخطاء
- إذا لم تكن متأكدًا من تشكيل كلمة، اكتبها بدون تشكيل بدلًا من تشكيل خاطئ
- الهدف هو تشكيل تعليمي واضح وصحيح، وليس تشكيلًا كاملاً بالقوة

مهم:
- لا تُرجع title أو narration_text بدون تشكيل كافٍ يساعد على القراءة
- لا تغيّر معنى النص
- حافظ على بساطة الجمل لتناسب الأطفال
- اجعل الجمل قصيرة وواضحة ومناسبة للنطق الصوتي

أنشئ EXACTLY {scenes} scenes. لا أكثر ولا أقل.

بيانات الطفل:
- name: {child_name}
- gender: {gender}
- appearance: {appearance}
- age_group: {age_group}

نوع القصة: {story_type}
السلوك المستهدف: {target_behavior}
الأسلوب الفني المطلوب: {image_style}
الوصف البصري المرجعي للأسلوب: {style_template}

مهم جدًا:
1) أعد JSON فقط.
2) title بالعربية مع التشكيل.
3) cover_prompt بالإنجليزية فقط، ويصف محتوى الغلاف ومشهده الرئيسي فقط.
4) لكل مشهد: narration_text بالعربية مع تشكيل تعليمي واضح وصحيح + image_prompt بالإنجليزية.
5) الطفل نفسه هو البطل في كل المشاهد مع اتساق الشكل.
6) image_prompt يجب أن يصف فقط محتوى المشهد: الشخصيات، الفعل، المكان، الوقت، العناصر المهمة، والمزاج.
7) لا تضف داخل image_prompt أو cover_prompt أي قواعد جودة عامة أو style أو no watermark أو no text، لأن النظام يضيفها تلقائيًا.
8) اجعل image_prompt و cover_prompt موجزين وواضحين ومناسبين مباشرة لتوليد الصورة.

صيغة الإخراج:
{{
  "title": "...",
  "cover_prompt": "...",
  "scenes": [
    {{
      "narration_text": "...",
      "image_prompt": "..."
    }}
  ]
}}
"""
    # This method generates a story package by sending a prompt to the LLM and expecting a structured JSON response that includes a title, cover prompt, and scenes with narration text and image prompts. The system prompt provided to the LLM includes detailed instructions in Arabic for how to format the story, the quality of the Arabic text, the use of diacritics, and the structure of the JSON response. The user prompt is passed as an argument, and the maximum token limit for the response can also be specified.
    async def generate_story_package(
        self,
        child_name,
        gender,
        appearance,
        age_group,
        story_type,
        target_behavior,
        image_style,
    ):
        prompt = self.build_prompt(
            child_name=child_name,
            gender=gender,
            appearance=appearance,
            age_group=age_group,
            story_type=story_type,
            target_behavior=target_behavior,
            image_style=image_style,
        )

        raw_story = await self.llm.generate_story_package(
            prompt,
            max_tokens=self._max_tokens(age_group),
        )

        try:
            normalized_story = await self.llm.normalize_story_package(raw_story)
            story = self._safe_normalize_story(raw_story, normalized_story)
        except Exception as e:
            print("NORMALIZE STORY FAILED:", e)
            story = raw_story

        scenes = story.get("scenes") or []

        if not scenes:
            raise Exception("No scenes generated")

        for scene in scenes:
            scene.setdefault("image", "")
            scene.setdefault("audio", "")

        story["child_name"] = child_name
        story["appearance"] = appearance
        story["age_group"] = age_group
        story["gender"] = gender
        story["story_type"] = story_type
        story["target_behavior"] = target_behavior
        story["image_style"] = image_style
        story["character_seed"] = self._character_seed(
            child_name=child_name,
            appearance=appearance,
            age_group=age_group,
            gender=gender,
            image_style=image_style,
        )
        story["cover_image"] = ""

        return story
    
    # This private method generates the necessary assets (images and audio) for a given scene in the story. It takes the scene data, an optional reference image, and various parameters related to the child and story. It uses the FluxService to generate an image based on the scene's image prompt and the TTSService to generate audio narration based on the scene's narration text. The generated image and audio are then added to the scene data, which is returned at the end.
    async def _generate_scene_assets(
        self,
        scene,
        reference_image=None,
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
        # Generate image and audio concurrently for the scene using asyncio.gather. The gen_image function uses the FluxService to generate an image based on the scene's image prompt and other parameters, while the gen_audio function uses the TTSService to generate audio narration based on the scene's narration text. If either generation fails, it falls back to any existing image or audio in the scene data.
        async def gen_image():
            try:
                return await self.flux.gen(
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
                print("SCENE IMAGE FAILED:", e)
                return scene.get("image") or ""
        
        # Generate image and audio concurrently for the scene using asyncio.gather. The gen_image function uses the FluxService to generate an image based on the scene's image prompt and other parameters, while the gen_audio function uses the TTSService to generate audio narration based on the scene's narration text. If either generation fails, it falls back to any existing image or audio in the scene data.
        async def gen_audio():
            try:
                return await self.tts.gen(scene.get("narration_text", ""))
            except Exception as e:
                print("SCENE AUDIO FAILED:", e)
                return scene.get("audio") or ""

        image, audio = await asyncio.gather(gen_image(), gen_audio())

        scene["image"] = image or scene.get("image") or ""
        scene["audio"] = audio or scene.get("audio") or ""

        return scene

    # This method generates the initial assets (images and audio) for a specified number of scenes in the story. It takes the story data, an optional reference image, and the count of scenes for which to generate assets immediately. It uses asyncio.gather to concurrently generate assets for the specified number of scenes by calling the _generate_scene_assets method for each scene. The generated assets are added to the story data, which is returned at the end.
    async def generate_initial_assets(
        self,
        story_data: dict,
        reference_image=None,
        immediate_count: int = 3,
    ):
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

        tasks = [
            self._generate_scene_assets(
                scenes[idx],
                reference_image,
                child_name=child_name,
                appearance=appearance,
                age_group=age_group,
                gender=gender,
                story_type=story_type,
                target_behavior=target_behavior,
                image_style=image_style,
                seed=seed,
            )
            for idx in range(immediate_count)
        ]

        if tasks:
            await asyncio.gather(*tasks)

        return story_data
    
    # This method generates the remaining assets (images and audio) for the scenes in the story that were not generated in the initial phase. It takes the story data, an optional reference image, and the starting index from which to generate assets for the remaining scenes. It uses a semaphore to limit the number of concurrent asset generation tasks to 3, and then calls the _generate_scene_assets method for each remaining scene. Additionally, it generates the cover image based on the cover prompt if it exists. The generated assets are added to the story data, which is returned at the end.
    async def generate_remaining_assets(
        self,
        story_data: dict,
        reference_image=None,
        start_index: int = 3,
    ):
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
        
        # Define an asynchronous function run_scene that takes a scene as input and generates the necessary assets for that scene using the _generate_scene_assets method. The function uses a semaphore to limit the number of concurrent executions to 3, ensuring that only a few scenes are processed at the same time to manage resource usage effectively.
        async def run_scene(scene):
            async with sem:
                return await self._generate_scene_assets(
                    scene,
                    reference_image,
                    child_name=child_name,
                    appearance=appearance,
                    age_group=age_group,
                    gender=gender,
                    story_type=story_type,
                    target_behavior=target_behavior,
                    image_style=image_style,
                    seed=seed,
                )

        scene_tasks = [run_scene(scene) for scene in scenes[start_index:]]
        
        # Define an asynchronous function run_cover that generates the cover image for the story based on the cover prompt. If the cover prompt is empty, it returns an empty string. Otherwise, it uses the FluxService to generate the cover image with the specified parameters. If the generation fails, it logs the error and returns any existing cover image from the story data or an empty string.
        async def run_cover():
            cover_prompt = (story_data.get("cover_prompt") or "").strip()

            if not cover_prompt:
                return ""

            try:
                return await self.flux.gen(
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
                )
            except Exception as e:
                print("COVER GENERATION FAILED:", e)
                return story_data.get("cover_image") or ""

        if scene_tasks:
            results = await asyncio.gather(*scene_tasks, run_cover())
        else:
            results = await asyncio.gather(run_cover())

        story_data["cover_image"] = results[-1] or story_data.get("cover_image") or ""

        return story_data
    
    # This method generates audio narration for a specific scene in the story based on the narration text. It takes the story data and the page index as input, retrieves the narration text for the specified page, and uses the TTSService to generate the audio. If the page index is invalid or if there is no narration text, it raises an exception. The generated audio is returned at the end.
    async def audio(self, story, page):
        scenes = story.get("scenes", [])

        if page >= len(scenes):
            raise Exception("Invalid page")

        text = (scenes[page].get("narration_text") or "").strip()

        if not text:
            raise Exception("No narration")

        return await self.tts.gen(text)