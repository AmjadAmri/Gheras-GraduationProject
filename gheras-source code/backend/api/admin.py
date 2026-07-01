# This module registers the models defined in the api.models module with the Django admin site. Each model is associated with a custom admin class that specifies how the model should be displayed and managed in the admin interface. The admin classes define the fields to be displayed in the list view, filters for easy navigation, search fields for quick access, and read-only fields to prevent modification of certain attributes. By registering these models with the admin site, administrators can easily manage the data related to behaviors, genres, art styles, children, stories, story pages, reading logs, and behavior tasks through a user-friendly interface.
from django.contrib import admin

# Import the models that will be registered with the admin site, including Behavior, Genre, ArtStyle, Child, Story, StoryPage, ReadingLog, and BehaviorTask. These models represent the core entities in the application and will be managed through the Django admin interface.
from api.models import (
    Behavior,
    Genre,
    ArtStyle,
    Child,
    Story,
    StoryPage,
    ReadingLog,
    BehaviorTask,
)

# Register the Behavior model with the admin site using the BehaviorAdmin class, which specifies the fields to be displayed in the list view, search fields for quick access, and any additional configurations for managing behaviors in the admin interface.
@admin.register(Behavior)
class BehaviorAdmin(admin.ModelAdmin):
    list_display = ["key", "label", "icon"]
    search_fields = ["key", "label", "description"]

# Register the Genre model with the admin site using the GenreAdmin class, which specifies the fields to be displayed in the list view, search fields for quick access, and any additional configurations for managing genres in the admin interface.
@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ["key", "label", "icon"]
    search_fields = ["key", "label", "description"]

# Register the ArtStyle model with the admin site using the ArtStyleAdmin class, which specifies the fields to be displayed in the list view, search fields for quick access, and any additional configurations for managing art styles in the admin interface.
@admin.register(ArtStyle)
class ArtStyleAdmin(admin.ModelAdmin):
    list_display = ["key", "label", "preview_url"]
    search_fields = ["key", "label", "description"]

# Register the Child model with the admin site using the ChildAdmin class, which specifies the fields to be displayed in the list view, filters for easy navigation, search fields for quick access, and any additional configurations for managing children in the admin interface.
@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "gender", "age_group"]
    list_filter = ["gender", "age_group"]
    search_fields = ["name", "user__email"]

# Register the Story model with the admin site using the StoryAdmin class, which specifies the fields to be displayed in the list view, filters for easy navigation, search fields for quick access, and read-only fields to prevent modification of certain attributes. This allows administrators to manage stories effectively through the admin interface.
@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "user",
        "child",
        "story_type",
        "art_style",
        "status",
        "pdf_status",
        "created_at",
    ]
    list_filter = [
        "status",
        "pdf_status",
        "story_type",
        "art_style",
    ]
    search_fields = [
        "title",
        "user__email",
        "child__name",
    ]
    readonly_fields = [
        "created_at",
        "pdf_file",
        "pdf_status",
    ]

# Register the StoryPage model with the admin site using the StoryPageAdmin class, which specifies the fields to be displayed in the list view, filters for easy navigation, search fields for quick access, and any additional configurations for managing story pages in the admin interface.
@admin.register(StoryPage)
class StoryPageAdmin(admin.ModelAdmin):
    list_display = [
        "story",
        "page_number",
        "has_image",
        "has_audio",
    ]
    list_filter = ["story"]
    search_fields = ["story__title", "narration_text"]

    # This method checks if the StoryPage instance has an associated illustration URL, indicating that an image has been generated for the page. It returns True if the illustration URL exists and is not empty, and False otherwise. This allows administrators to quickly see which story pages have images available in the admin list view.
    def has_image(self, obj):
        return bool(obj.illustration_url)

    has_image.boolean = True
    has_image.short_description = "Image"

    # This method checks if the StoryPage instance has an associated audio URL, indicating that an audio file has been generated for the narration text. It returns True if the audio URL exists and is not empty, and False otherwise. This allows administrators to quickly see which story pages have audio content available in the admin list view.
    def has_audio(self, obj):
        return bool(obj.audio_url)

    has_audio.boolean = True
    has_audio.short_description = "Audio"

# Register the ReadingLog model with the admin site using the ReadingLogAdmin class, which specifies the fields to be displayed in the list view, filters for easy navigation, search fields for quick access, and read-only fields to prevent modification of certain attributes. This allows administrators to manage reading logs effectively through the admin interface.
@admin.register(ReadingLog)
class ReadingLogAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "child",
        "story",
        "time_spent",
        "started_at",
        "finished_at",
    ]
    list_filter = ["finished_at"]
    search_fields = ["user__email", "child__name", "story__title"]
    readonly_fields = ["started_at"]

# Register the BehaviorTask model with the admin site using the BehaviorTaskAdmin class, which specifies the fields to be displayed in the list view, filters for easy navigation, search fields for quick access, and read-only fields to prevent modification of certain attributes. This allows administrators to manage behavior tasks effectively through the admin interface.
@admin.register(BehaviorTask)
class BehaviorTaskAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "child",
        "story",
        "behavior",
        "response",
        "created_at",
    ]
    list_filter = ["behavior", "response"]
    search_fields = ["user__email", "child__name", "behavior"]
    readonly_fields = ["created_at"]
