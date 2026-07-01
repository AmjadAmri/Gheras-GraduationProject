# This script is used to seed the database with initial data for behaviors, genres, and art styles. It defines lists of dictionaries for each category, where each dictionary contains the key, label, icon, and description for a specific behavior, genre, or art style. The script then iterates through each list and uses the get_or_create method to add the entries to the database if they do not already exist. Finally, it prints the count of each category and a completion message.
# import necessary modules and functions, including the app module to set up the Django environment and the Behavior, Genre, and ArtStyle models to interact with the database.
import app

from api.models import Behavior, Genre, ArtStyle

# Define lists of dictionaries for behaviors, genres, and art styles, where each dictionary contains the key, label, icon, and description for a specific entry in each category. These lists will be used to seed the database with initial data.
BEHAVIORS = [
    {"key": "courage", "label": "الشجاعة", "icon": "Shield", "description": "تعزيز الثقة بالنفس والشجاعة"},
    {"key": "kindness", "label": "اللطف", "icon": "Heart", "description": "التعامل بلطف مع الآخرين"},
    {"key": "sharing", "label": "المشاركة", "icon": "HandHeart", "description": "تعلّم مشاركة الأشياء مع الآخرين"},
    {"key": "honesty", "label": "الصدق", "icon": "Star", "description": "أهمية قول الحقيقة دائماً"},
    {"key": "responsibility", "label": "المسؤولية", "icon": "ClipboardCheck", "description": "تحمّل المسؤولية والاعتماد على النفس"},
    {"key": "patience", "label": "الصبر", "icon": "Clock", "description": "التحلّي بالصبر وعدم الاستعجال"},
    {"key": "respect", "label": "الاحترام", "icon": "Crown", "description": "احترام الآخرين والاختلاف"},
    {"key": "gratitude", "label": "الامتنان", "icon": "Gift", "description": "تقدير النعم وشكر الآخرين"},
    {"key": "empathy", "label": "التعاطف", "icon": "Heart", "description": "فهم مشاعر الآخرين والتعاطف معهم"},
    {"key": "other", "label": "أخرى", "icon": "PenLine", "description": "سلوك مخصص من اختيارك"},
]

# Define a list of dictionaries for genres, where each dictionary contains the key, label, icon, and description for a specific genre. This list will be used to seed the database with initial genre data.
GENRES = [
    {"key": "adventure", "label": "مغامرة", "icon": "Compass", "description": "قصص مليئة بالمغامرات والاستكشاف"},
    {"key": "fantasy", "label": "خيال", "icon": "Sparkles", "description": "عوالم سحرية وشخصيات خيالية"},
    {"key": "educational", "label": "تعليمية", "icon": "GraduationCap", "description": "تعلّم مفاهيم جديدة بطريقة ممتعة"},
    {"key": "social", "label": "اجتماعية", "icon": "Users", "description": "مهارات التواصل والعلاقات"},
    {"key": "nature", "label": "طبيعة", "icon": "TreePine", "description": "استكشاف الطبيعة والحيوانات"},
    {"key": "space", "label": "فضاء", "icon": "Rocket", "description": "رحلات إلى الفضاء والكواكب"},
]

# Define a list of dictionaries for art styles, where each dictionary contains the key, label, preview URL, and description for a specific art style. This list will be used to seed the database with initial art style data.
ART_STYLES = [
    {
        "key": "storybook",
        "label": "كتاب أطفال",
        "preview_url": "https://placehold.co/200x150/4ECDC4/white?text=Storybook",
        "description": "أسلوب كتب الأطفال الكلاسيكي برسومات لطيفة",
    },
    {
        "key": "cartoon",
        "label": "كرتون",
        "preview_url": "https://placehold.co/200x150/FF6B6B/white?text=Cartoon",
        "description": "رسومات كرتونية مرحة وملونة",
    },
    {
        "key": "watercolor",
        "label": "ألوان مائية",
        "preview_url": "https://placehold.co/200x150/87CEEB/white?text=Watercolor",
        "description": "رسومات ناعمة بألوان مائية دافئة",
    },
    {
        "key": "paper",
        "label": "قص ولصق",
        "preview_url": "https://placehold.co/200x150/F59E0B/white?text=Paper",
        "description": "أسلوب القص واللصق الورقي",
    },
    {
        "key": "pixel",
        "label": "بكسل آرت",
        "preview_url": "https://placehold.co/200x150/EC4899/white?text=Pixel",
        "description": "رسومات رقمية بأسلوب البكسل",
    },
    {
        "key": "anime",
        "label": "أنمي",
        "preview_url": "https://placehold.co/200x150/A78BFA/white?text=Anime",
        "description": "رسومات بأسلوب الأنمي الياباني",
    },
    
]

# This function seeds the database with the predefined behaviors, genres, and art styles. It iterates through each list of data and uses the get_or_create method to add entries to the database if they do not already exist. After seeding each category, it prints the count of entries in that category and a completion message at the end.
def seed():
    for data in BEHAVIORS:
        Behavior.objects.get_or_create(key=data["key"], defaults=data)
    print(f"Behaviors: {Behavior.objects.count()}")

    for data in GENRES:
        Genre.objects.get_or_create(key=data["key"], defaults=data)
    print(f"Genres: {Genre.objects.count()}")

    for data in ART_STYLES:
        ArtStyle.objects.get_or_create(key=data["key"], defaults=data)
    print(f"ArtStyles: {ArtStyle.objects.count()}")

    print("Seed complete.")

# If this script is run directly, call the seed function to populate the database with the initial data for behaviors, genres, and art styles.
if __name__ == "__main__":
    seed()
