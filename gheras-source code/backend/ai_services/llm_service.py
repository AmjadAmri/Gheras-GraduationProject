# This module defines the LLMService class, which provides methods for interacting with a language model to generate and normalize story packages for children's stories in Arabic. The service uses the OpenAI API to send prompts and receive structured JSON responses that include story titles, narration texts, and image prompts. It also includes functionality to calculate diacritic ratios in Arabic text and determine if a story needs more diacritics based on a specified threshold. The generated story packages can be normalized to ensure consistent formatting before being used in the application.
# Import necessary libraries for JSON handling, environment variable access, regular expressions, and the OpenAI API client
import json
import os
import re
from openai import AsyncOpenAI

# Define the LLMService class that provides methods for interacting with a language model to generate and normalize story packages for children's stories in Arabic. It includes methods for sending prompts to the LLM, calculating diacritic ratios, determining if a story needs more diacritics, generating story packages based on user prompts, and normalizing the structure of the generated story packages.
class LLMService:
    
    # Initialize the LLMService by creating an instance of the AsyncOpenAI client using the API key from environment variables
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # This private method sends a chat completion request to the OpenAI API with the specified system prompt, user prompt, and maximum token limit. It expects the response to be in JSON format and parses it accordingly. If the response is empty or cannot be parsed as JSON, it raises an exception.
    async def _chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4800,
    ):
        res = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.3,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
        )

        content = res.choices[0].message.content

        print("\n===== JSON FROM LLM =====")
        print(content)
        print("=========================\n")

        if not content:
            raise Exception("LLM returned empty response")

        return json.loads(content)

    # This private method calculates the ratio of diacritic characters to Arabic letters in a given text. It uses regular expressions to find all Arabic letters and diacritic characters, and then computes the ratio. If there are no Arabic letters, it returns 0.0 to avoid division by zero.
    def _diacritic_ratio(self, text: str) -> float:
        arabic_letters = re.findall(r"[\u0621-\u064A]", text or "")
        diacritics = re.findall(r"[\u064B-\u0652]", text or "")

        if not arabic_letters:
            return 0.0

        return len(diacritics) / len(arabic_letters)
    
    # This private method checks if a given story dictionary needs more diacritics based on the ratio of diacritic characters to Arabic letters in the title and narration texts. It combines the title and narration texts into a single string and calculates the diacritic ratio. If the ratio is below a specified minimum threshold (default is 0.35), it returns True, indicating that the story needs more diacritics; otherwise, it returns False.
    def _story_needs_diacritics(
        self,
        story: dict,
        min_ratio: float = 0.35,
    ) -> bool:
        if not isinstance(story, dict):
            return True

        title = story.get("title", "")
        scenes = story.get("scenes") or []

        texts = [title]
        texts.extend(scene.get("narration_text", "") for scene in scenes)

        full_text = " ".join(texts)
        return self._diacritic_ratio(full_text) < min_ratio

    # This method generates a story package by sending a prompt to the LLM and expecting a structured JSON response that includes a title, cover prompt, and scenes with narration text and image prompts. The system prompt provided to the LLM includes detailed instructions in Arabic for how to format the story, the quality of the Arabic text, the use of diacritics, and the structure of the JSON response. The user prompt is passed as an argument, and the maximum token limit for the response can also be specified.
    async def generate_story_package(self, prompt: str, max_tokens: int):
        return await self._chat_json(
            system_prompt=(
    "أنتَ كاتب قصص أطفال عربي محترف، ومهندس أوامر بصرية متخصص في كتابة أوصاف الصور. "
    "مهمتك كتابة قصة أطفال عربية سليمة لغويًا، مع إنشاء image_prompt و cover_prompt مناسبين لتوليد الصور. "
    "اكتب title وكل narration_text باللغة العربية الفصحى الصحيحة، وبتشكيل واضح وصحيح ومناسب للأطفال. "
    "النص الموجود في narration_text هو النص النهائي الذي سيُعرض للطفل ويُستخدم مباشرة في TTS، لذلك يجب أن يكون واضحًا وسليمًا وقابلًا للنطق. "
    
    "قواعد جودة النص العربي: "
    "- استخدم كلمات عربية صحيحة ومفهومة فقط. "
    "- ممنوع استخدام كلمات مشوهة أو غير موجودة في العربية أو غير مفهومة. "
    "- قبل إخراج JSON النهائي، راجع كل narration_text وتأكد أن كل كلمة سليمة وواضحة. "
    "- إذا ظهرت كلمة غير واضحة أو غير دقيقة، استبدلها بكلمة عربية بسيطة وصحيحة قبل الإخراج. "
    "- حافظ على الجمل قصيرة وطبيعية ومناسبة لعمر الطفل. "
    
    "قواعد التشكيل: "
    "- يجب أن يكون التشكيل دقيقًا وليس عشوائيًا أو زخرفيًا. "
    "- استخدم الحركات الأساسية عند الحاجة: الفتحة، الضمة، الكسرة، السكون، الشدة، والتنوين الواضح عند التأكد. "
    "- ركّز على وضوح قراءة الكلمة للطفل أكثر من الإعراب الكامل لكل كلمة. "
    "- راعِ قواعد النحو والإملاء، خصوصًا في الكلمات الشائعة والبسيطة. "
    "- لا تضع حركة إعرابية إذا لم تكن متأكدًا منها. "
    "- لا تضف تشكيلًا على كلمة إذا كان سيجعلها نحويًا غير صحيحة. "
    "- إذا لم تكن متأكدًا من تشكيل كلمة، اكتبها بدون تشكيل بدلًا من تشكيل خاطئ. "
    "- لا تستخدم تشكيلًا عشوائيًا أو متناقضًا داخل الجملة. "
    "- تجنّب المبالغة في التشكيل؛ المطلوب تشكيل تعليمي واضح ودقيق، وليس تشكيلًا كاملًا بالقوة. "
    
    "أمثلة توجيهية: "
    "- اكتب كلمات واضحة مثل: فِي الْحَدِيقَةِ، فِي الْبِرْكَةِ، مَعَ أَصْدِقَائِهَا، إذا كان السياق مناسبًا. "
    "- لا تُخرج كلمات مشوهة مثل: الْتٍاصَ أو أي كلمة غير مفهومة. "
    "- لا تخمّن حركة آخر الكلمة إذا لم تكن متأكدًا من موقعها الإعرابي. "
    
    "اكتب image_prompt و cover_prompt باللغة الإنجليزية فقط، ويجب أن تكون أوصافًا بصرية واضحة ومباشرة. "
    "لا تضع داخل image_prompt أو cover_prompt أي نص عربي أو تشكيل عربي. "
    "التزم ببنية JSON المطلوبة فقط. "
    "لا تكتب أي شرح أو تعليق أو نص خارج JSON."
   
            ),
            user_prompt=prompt,
            max_tokens=max_tokens,
        )

   # This method takes a story package in the form of a dictionary and normalizes its structure by ensuring that the title, cover prompt, and narration texts are all stripped of leading and trailing whitespace. It also ensures that the scenes are properly structured with the expected keys. The method returns a cleaned version of the story package that is ready for use in the application.
    async def normalize_story_package(self, story: dict):
        if not isinstance(story, dict):
            raise Exception("Story is not a dict")

        title = (story.get("title") or "").strip()
        cover_prompt = (story.get("cover_prompt") or "").strip()
        scenes = story.get("scenes") or []

        cleaned = {
            "title": title,
            "cover_prompt": cover_prompt,
            "scenes": [],
        }

        for scene in scenes:
            cleaned["scenes"].append(
                {
                    "narration_text": (
                        scene.get("narration_text") or ""
                    ).strip(),
                    "image_prompt": (
                        scene.get("image_prompt") or ""
                    ).strip(),
                }
            )
        
        return cleaned