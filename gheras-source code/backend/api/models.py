# This code defines the data models for a storytelling application using Django's ORM. It includes models for Child, Story, StoryPage, ReadingLog, BehaviorTask, Behavior, Genre, and ArtStyle. Each model has fields that represent the attributes of the respective entities, along with relationships between them. The models also include metadata for ordering and string representations for easy identification in the admin interface and other parts of the application.
from django.db import models
from django.conf import settings

# Define the Child model, which represents a child user in the application. It includes fields for the user's
class Child(models.Model):
    
    AGE_GROUP_CHOICES = [
        ("4-5", "4-5"),
        ("6-7", "6-7"),
        ("8-9", "8-9"),
    ]

    GENDER_CHOICES = [("boy", "Boy"), ("girl", "Girl")]
    
    # The user field is a foreign key that links the Child model to the Django user model, allowing each child to be associated with a specific user account. This relationship enables personalized experiences and data management for each child within the application.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="children",
    )
    
    # The name field is a character field that stores the name of the child. It has a maximum length of 100 characters and is required for each child instance.
    name = models.CharField(max_length=100)
    
    # The gender field is a character field that stores the gender of the child. It uses predefined choices (boy or girl) to ensure data consistency and is required for each child instance.
    gender = models.CharField(
        max_length=4,
        choices=GENDER_CHOICES,
    )

    age_group = models.CharField(
        max_length=3,
        choices=AGE_GROUP_CHOICES,
        default="6-7",
    )
    
    # The avatar_url field is a URL field that can store the URL of the child's avatar image. It is optional and defaults to an empty string if not provided.
    avatar_url = models.URLField(blank=True, default="")
    appearance_description = models.TextField(blank=True, default="")
    photo = models.ImageField(upload_to="children/", blank=True, null=True)
    
    # The Meta class defines the ordering of Child instances when queried from the database. In this case, it orders the children by their ID in ascending order.
    class Meta:
        ordering = ["id"]
    
    # The __str__ method provides a string representation of the Child instance, which is useful for displaying the child's name in the admin interface and other parts of the application where a string representation is needed.
    def __str__(self):
        return self.name

# Define the Story model, which represents a story created for a child. It includes fields for the user who created the story, the child for whom the story is created, the title of the story, cover image URL, story type, art style, target behavior, custom behavior, status of the story generation process, raw JSON data of the story, PDF file for download, PDF generation status and progress, and timestamps for creation. The Story model also defines choices for status and PDF status to track the progress of story generation and PDF creation.
class Story(models.Model):
    
    # Define choices for the status of the story generation process, which include queued, generating story, generating images, ready, and failed. These choices help track the current state of the story as it goes through the generation pipeline.
    STATUS_CHOICES = [
        ("queued", "Queued"),
        ("generating_story", "Generating Story"),
        ("generating_images", "Generating Images"),
        ("ready", "Ready"),
        ("failed", "Failed"),
    ]
    
    # Define choices for the PDF generation status, which include pending, generating, ready, and failed. These choices help track the progress of PDF creation for the story, allowing the application to provide feedback to users about the availability of the downloadable PDF version of the story.
    PDF_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("generating", "Generating"),
        ("ready", "Ready"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="stories",
    )

    child = models.ForeignKey(
        Child,
        on_delete=models.CASCADE,
        related_name="stories",
    )

    title = models.CharField(max_length=255, blank=True, default="")
    cover_url = models.URLField(max_length=1000, blank=True, default="")

    story_type = models.CharField(max_length=50)
    art_style = models.CharField(max_length=50)
    target_behavior = models.CharField(max_length=50)
    custom_behavior = models.CharField(max_length=100, blank=True, default="")

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="queued",
    )

    raw_story_json = models.JSONField(null=True, blank=True)

    pdf_file = models.FileField(
        upload_to="pdfs/",
        blank=True,
        null=True,
    )

    pdf_status = models.CharField(
        max_length=20,
        choices=PDF_STATUS_CHOICES,
        default="pending",
    )

    pdf_progress = models.IntegerField(default=0)

    pdf_error = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

# Define the StoryPage model, which represents a single page of a story. It includes fields for the associated story, page number, narration text, illustration URL, audio URL, and a hash of the audio text for caching purposes. The StoryPage model also defines metadata for ordering pages by their page number and provides a string representation that includes the story title and page number for easy identification.
class StoryPage(models.Model):

    story = models.ForeignKey(
        Story,
        on_delete=models.CASCADE,
        related_name="pages",
    )

    page_number = models.IntegerField()
    narration_text = models.TextField()
    illustration_url = models.TextField(blank=True, default="")
    audio_url = models.TextField(blank=True, default="")
    audio_text_hash = models.CharField(max_length=32, blank=True, default="")
    
    class Meta:
        ordering = ["page_number"]

    def __str__(self):
        return f"{self.story.title} - Page {self.page_number}"

# Define the ReadingLog model, which represents a log of a child reading a story. It includes fields for the user, child, story, timestamps for when the reading started and finished, and the time spent reading in seconds. The ReadingLog model also defines metadata for ordering logs by the start time and provides a string representation that includes the child's name and the story title for easy identification.
class ReadingLog(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reading_logs",
    )

    child = models.ForeignKey(
        Child,
        on_delete=models.CASCADE,
        related_name="reading_logs",
    )

    story = models.ForeignKey(
        Story,
        on_delete=models.CASCADE,
        related_name="reading_logs",
    )

    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    time_spent = models.IntegerField(
        default=0,
        help_text="Time spent reading in seconds",
    )

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.child.name} read {self.story.title}"


class BehaviorTask(models.Model):

    RESPONSE_CHOICES = [
        ("yes", "Yes"),
        ("try", "I'll try"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="behavior_tasks",
    )

    child = models.ForeignKey(
        Child,
        on_delete=models.CASCADE,
        related_name="behavior_tasks",
    )

    story = models.ForeignKey(
        Story,
        on_delete=models.CASCADE,
        related_name="behavior_tasks",
    )

    behavior = models.CharField(max_length=50)

    response = models.CharField(
        max_length=10,
        choices=RESPONSE_CHOICES,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.child.name} - {self.behavior} ({self.response})"

# Define the Behavior model, which represents a specific behavior that can be targeted in a story. It includes fields for a unique key, a label for display purposes, an optional icon, and a description. The Behavior model also defines metadata for ordering behaviors by their ID and provides a string representation that returns the label of the behavior for easy identification.
class Behavior(models.Model):

    key = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True, default="")
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.label

# Define the Genre model, which represents a genre that can be associated with a story. It includes fields for a unique key, a label for display purposes, an optional icon, and a description. The Genre model also defines metadata for ordering genres by their ID and provides a string representation that returns the label of the genre for easy identification.
class Genre(models.Model):

    key = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True, default="")
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.label

# Define the ArtStyle model, which represents an art style that can be associated with a story. It includes fields for a unique key, a label for display purposes, a preview URL for showcasing the art style, and a description. The ArtStyle model also defines metadata for ordering art styles by their ID and provides a string representation that returns the label of the art style for easy identification.
class ArtStyle(models.Model):

    key = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=100)
    preview_url = models.URLField(blank=True, default="")
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.label