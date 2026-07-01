# import necessary modules and classes from datetime, time, and typing for handling dates, times, and type annotations
from django.contrib.auth.models import User
from rest_framework import serializers
import re

from api.models import (
    Child,
    Story,
    StoryPage,
    ReadingLog,
    BehaviorTask,
    Behavior,
    Genre,
    ArtStyle,
)

# Define serializers for the User, Child, StoryPage, Story, ReadingLog, and BehaviorTask models. These serializers are used to convert model instances to JSON format and validate incoming data for creating or updating instances through the API. Each serializer specifies the fields to be included in the serialized output and any additional validation logic required for specific fields.
class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="first_name")
    
    # The Meta class specifies the model to be serialized (User) and the fields to be included in the serialized output, which are the user's ID, name (mapped from first_name), and email address. This serializer can be used to represent user data in API responses or to validate incoming data when creating or updating user instances.
    class Meta:
        model = User
        fields = ["id", "name", "email"]

# The ChildSerializer class is a serializer for the Child model. It includes fields for the child's ID,
class ChildSerializer(serializers.ModelSerializer):
    storiesCount = serializers.IntegerField(source="stories.count", read_only=True)
    avatarUrl = serializers.URLField(source="avatar_url", required=False, allow_blank=True)
    ageGroup = serializers.CharField(source="age_group")
    appearanceDescription = serializers.CharField(
        source="appearance_description",
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = Child
        fields = [
            "id",
            "name",
            "gender",
            "ageGroup",
            "avatarUrl",
            "appearanceDescription",
            "photo",
            "storiesCount",
        ]
    
    # The create method is overridden to automatically associate the child instance being created with the currently authenticated user. When a new child instance is created through the API, the user field of the Child model will be set to the user making the request, ensuring that each child is linked to a specific user in the database. This allows for proper ownership and access control of child instances in the application.
    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)

# The StoryPageSerializer class is a serializer for the StoryPage model. It includes fields for the page number, narration text, illustration URL, and audio URL. The field names in the serialized output are mapped to more user-friendly names (e.g., pageNumber, narrationText) using the source attribute. This serializer can be used to represent story page data in API responses or to validate incoming data when creating or updating story page instances.
class StoryPageSerializer(serializers.ModelSerializer):
    pageNumber = serializers.IntegerField(source="page_number")
    narrationText = serializers.CharField(source="narration_text", allow_blank=True)
    illustrationUrl = serializers.CharField(
        source="illustration_url",
        required=False,
        allow_blank=True,
    )
    audioUrl = serializers.CharField(
        source="audio_url",
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = StoryPage
        fields = ["pageNumber", "narrationText", "illustrationUrl", "audioUrl"]

# The StorySerializer class is a serializer for the Story model. It includes fields for the story's ID, title, child information, cover URL, story type, art style, target behavior, custom behavior, status, pages, PDF generation status and progress, and creation timestamp. The serializer also includes a method to determine if the PDF is ready based on the PDF status and file availability. The create method is overridden to associate the story instance being created with the currently authenticated user. This serializer can be used to represent story data in API responses or to validate incoming data when creating or updating story instances.
class StorySerializer(serializers.ModelSerializer):
    pages = StoryPageSerializer(many=True, read_only=True)

    childId = serializers.PrimaryKeyRelatedField(
        source="child",
        queryset=Child.objects.all(),
    )

    childName = serializers.CharField(source="child.name", read_only=True)
    coverUrl = serializers.URLField(source="cover_url", required=False, allow_blank=True)

    storyType = serializers.CharField(source="story_type")
    artStyle = serializers.CharField(source="art_style")
    targetBehavior = serializers.CharField(source="target_behavior")

    customBehavior = serializers.CharField(
        source="custom_behavior",
        read_only=True,
        allow_blank=True,
    )

    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    pdfStatus = serializers.CharField(source="pdf_status", read_only=True)
    pdfProgress = serializers.IntegerField(source="pdf_progress", read_only=True)
    pdfError = serializers.CharField(source="pdf_error", read_only=True)
    pdfUrl = serializers.FileField(source="pdf_file", read_only=True)
    pdfReady = serializers.SerializerMethodField()

    # The Meta class specifies the model to be serialized (Story) and the fields to be included in the serialized output. It also defines a method get_pdfReady to determine if the PDF is ready based on the PDF status and file availability. The create method is overridden to automatically associate the story instance being created with the currently authenticated user, ensuring that each story is linked to a specific user in the database for proper ownership and access control.
    class Meta:
        model = Story
        fields = [
            "id",
            "title",
            "childId",
            "childName",
            "coverUrl",
            "storyType",
            "artStyle",
            "targetBehavior",
            "customBehavior",
            "status",
            "pages",
            "pdfStatus",
            "pdfProgress",
            "pdfError",
            "pdfReady",
            "pdfUrl",
            "createdAt",
        ]
    
    # This method checks if the PDF for the story is ready by verifying that the pdf_status is "ready" and that a pdf_file exists. It returns True if both conditions are met, indicating that the PDF is ready for download or viewing, and False otherwise. This method is used as a SerializerMethodField to provide a convenient way to check the PDF readiness status in API responses.
    def get_pdfReady(self, obj):
        return obj.pdf_status == "ready" and bool(obj.pdf_file)

    # The create method is overridden to automatically associate the story instance being created with the currently authenticated user. When a new story instance is created through the API, the user field of the Story model will be set to the user making the request, ensuring that each story is linked to a specific user in the database. This allows for proper ownership and access control of story instances in the application.
    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)

# The ReadingLogCreateSerializer class is a serializer for creating ReadingLog instances. It includes fields for the child ID, story ID, time spent reading, and whether the story was finished. This serializer can be used to validate incoming data when creating new reading log entries through the API.
class StoryCreateSerializer(serializers.Serializer):
    childId = serializers.IntegerField()
    storyType = serializers.CharField(max_length=50)
    artStyle = serializers.CharField(max_length=50)
    targetBehavior = serializers.CharField(max_length=50)

    customBehavior = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        default="",
    )

    # The validate method is overridden to ensure that if the target behavior is set to "other", a custom behavior must be provided. If the target behavior is "other" and the custom behavior field is empty, a ValidationError is raised with an appropriate error message. This validation logic ensures that when users select "other" as the target behavior, they are required to specify what that behavior is in the customBehavior field, maintaining data integrity and providing necessary information for story generation.
    def validate(self, attrs):
        target_behavior = (attrs.get("targetBehavior") or "").strip()
        custom_behavior = (attrs.get("customBehavior") or "").strip()

        # If the target behavior is "other" and the custom behavior field is empty, raise a ValidationError to indicate that the custom behavior must be provided when "other" is selected as the target behavior. This ensures that users provide necessary information for story generation when they choose "other" as the target behavior.
        if target_behavior == "other" and not custom_behavior:
            raise serializers.ValidationError(
                {
                    "customBehavior": "يجب كتابة السلوك المطلوب عند اختيار (أخرى)."
                }
            )

        invalid_custom_behavior_pattern = r"(.)\1{3,}|[^\u0600-\u06FF\s،؟.!-]"

        if target_behavior == "other" and re.search(invalid_custom_behavior_pattern, custom_behavior):
            raise serializers.ValidationError(
                {
                    "customBehavior": "يرجى إدخال سلوك مفهوم باللغة العربية فقط."
                }
            )
    
        return attrs

# The ReadingLogSerializer class is a serializer for the ReadingLog model. It includes fields for the child ID, story ID, story title, time spent reading, start and finish timestamps. The childId and storyId fields are read-only and are represented as primary key related fields, while the storyTitle is a read-only field that retrieves the title of the associated story. This serializer can be used to represent reading log data in API responses or to validate incoming data when creating or updating reading log instances.
class ReadingLogCreateSerializer(serializers.Serializer):
    childId = serializers.IntegerField()
    storyId = serializers.IntegerField()
    timeSpent = serializers.IntegerField(required=False, default=0)
    finished = serializers.BooleanField(required=False, default=False)

# The BehaviorTaskCreateSerializer class is a serializer for creating BehaviorTask instances. It includes fields for the child ID, story ID, behavior, and response. This serializer can be used to validate incoming data when creating new behavior task entries through the API.
class ReadingLogSerializer(serializers.ModelSerializer):
    childId = serializers.PrimaryKeyRelatedField(source="child", read_only=True)
    storyId = serializers.PrimaryKeyRelatedField(source="story", read_only=True)
    storyTitle = serializers.CharField(source="story.title", read_only=True)
    timeSpent = serializers.IntegerField(source="time_spent")
    startedAt = serializers.DateTimeField(source="started_at", read_only=True)
    finishedAt = serializers.DateTimeField(source="finished_at", read_only=True)

    class Meta:
        model = ReadingLog
        fields = [
            "id",
            "childId",
            "storyId",
            "storyTitle",
            "timeSpent",
            "startedAt",
            "finishedAt",
        ]

# The BehaviorTaskCreateSerializer class is a serializer for creating BehaviorTask instances. It includes fields for the child ID, story ID, behavior, and response. This serializer can be used to validate incoming data when creating new behavior task entries through the API.
class BehaviorTaskCreateSerializer(serializers.Serializer):
    childId = serializers.IntegerField()
    storyId = serializers.IntegerField()
    behavior = serializers.CharField(max_length=50)
    response = serializers.ChoiceField(choices=["yes", "try"])

# The BehaviorTaskSerializer class is a serializer for the BehaviorTask model. It includes fields for the child ID, story ID, behavior, response, and creation timestamp. The childId and storyId fields are read-only and are represented as primary key related fields, while the createdAt field is a read-only DateTimeField that retrieves the creation timestamp of the behavior task. This serializer can be used to represent behavior task data in API responses or to validate incoming data when creating or updating behavior task instances.
class BehaviorTaskSerializer(serializers.ModelSerializer):
    childId = serializers.PrimaryKeyRelatedField(source="child", read_only=True)
    storyId = serializers.PrimaryKeyRelatedField(source="story", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = BehaviorTask
        fields = ["id", "childId", "storyId", "behavior", "response", "createdAt"]

# The BehaviorSerializer, GenreSerializer, and ArtStyleSerializer classes are serializers for the Behavior, Genre, and ArtStyle models, respectively. Each serializer includes fields for the model's ID, key, label, icon, and description. The ArtStyleSerializer also includes a previewUrl field that maps to the preview_url attribute of the ArtStyle model. These serializers can be used to represent behavior, genre, and art style data in API responses or to validate incoming data when creating or updating instances of these models.
class BehaviorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Behavior
        fields = ["id", "key", "label", "icon", "description"]

# The GenreSerializer class is a serializer for the Genre model. It includes fields for the genre's ID, key, label, icon, and description. This serializer can be used to represent genre data in API responses or to validate incoming data when creating or updating genre instances.
class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["id", "key", "label", "icon", "description"]

# The ArtStyleSerializer class is a serializer for the ArtStyle model. It includes fields for the art style's ID, key, label, preview URL, and description. The previewUrl field is mapped to the preview_url attribute of the ArtStyle model, allowing for a more user-friendly field name in API responses. This serializer can be used to represent art style data in API responses or to validate incoming data when creating or updating art style instances.
class ArtStyleSerializer(serializers.ModelSerializer):
    previewUrl = serializers.URLField(
        source="preview_url",
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = ArtStyle
        fields = ["id", "key", "label", "previewUrl", "description"]