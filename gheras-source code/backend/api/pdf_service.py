# This module provides functionality for generating PDF versions of stories created in the application. It includes functions for drawing the cover page and individual story pages, as well as a main function to build the PDF bytes and save the PDF file associated with a story. The PDF generation process includes handling text shaping for Arabic script, image resolution and fitting, and progress updates to track the generation status. The generated PDF files are stored in the media directory and can be accessed via their URLs once ready.
# Import necessary libraries and modules, including io for handling byte streams, re for regular expressions, unicodedata for Unicode normalization, pathlib for file path handling, Django settings and ContentFile for file management, httpx for making HTTP requests, PIL for image processing, and arabic_reshaper and bidi for handling Arabic text shaping and bidirectional display.
import io
import re
import unicodedata
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile

import httpx
from PIL import Image, ImageDraw, ImageFont

import arabic_reshaper
from bidi.algorithm import get_display

# Define constants for page dimensions, margins, panel widths, background colors, text colors, and font paths. These constants are used throughout the PDF generation process to ensure consistent styling and layout of the generated PDF pages.
PAGE_W = 1600
PAGE_H = 1000
MARGIN = 40
TEXT_PANEL_W = 600
IMAGE_PANEL_W = PAGE_W - (MARGIN * 3) - TEXT_PANEL_W

BOOK_BG = "#e8e3d8"
CARD_BG = "#ffffff"
TEXT_BG = "#f7f7f7"
IMAGE_BG = "#18c08c"
TEXT_COLOR = "#374151"
MUTED_COLOR = "#9ca3af"
BASE_DIR = Path(__file__).resolve().parents[1]

_FONT_CANDIDATES_REGULAR = [
    BASE_DIR / "fonts" / "NotoNaskhArabic-Regular.ttf",
]

_FONT_CANDIDATES_BOLD = [
    BASE_DIR / "fonts" / "NotoNaskhArabic-Bold.ttf",
]

# Helper function to pick the first existing font from a list of candidate font paths. It iterates through the provided list of font paths and checks if each path exists. If a valid font file is found, it returns the string representation of that path; otherwise, it returns None. This function is used to determine which font files are available for use in the PDF generation process.
def _pick_font(candidates):
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


FONT_PATH = _pick_font(_FONT_CANDIDATES_REGULAR)
FONT_BOLD_PATH = _pick_font(_FONT_CANDIDATES_BOLD)

# Define a function to load a font with a specified size. It attempts to load the font from the provided path and falls back to the default font if loading fails. This function is used to ensure that a valid font is available for rendering text in the PDF, even if the specified font files are not found or cannot be loaded.
def _font(path: str | None, size: int):
    if path:
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            pass

    return ImageFont.load_default()

# Define a function to clean and normalize text extracted from PDFs. It removes unwanted Unicode characters, normalizes the text to NFC form, replaces certain punctuation marks with their Arabic equivalents, and collapses multiple whitespace characters into a single space. This function is essential for ensuring that the text extracted from PDFs is clean and properly formatted for further processing, such as shaping for Arabic script and rendering in the generated PDF.
def _clean_pdf_text(text: str) -> str:
    text = str(text or "")

    text = re.sub(r"[\u200e\u200f\u202a-\u202e\u2066-\u2069]", "", text)
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r'[\"“”‘’«»]', "", text)

    text = text.replace("：", "،")
    text = text.replace("！", "!")
    text = text.replace(":", "،")
    text = text.replace(";", "؛")
    text = text.replace("?", "؟")
    text = text.replace("\ufffd", "")

    text = re.sub(r"\s+", " ", text).strip()

    return text

# Define a function to shape Arabic text for proper display in the PDF. It first cleans the input text using the _clean_pdf_text function, then uses the arabic_reshaper library to reshape the text according to specified options for handling diacritics and ligatures. Finally, it applies the get_display function from the bidi library to ensure that the reshaped text is displayed correctly in a right-to-left context. If any step in the shaping process fails, it returns the cleaned text as a fallback.
def _shape_arabic(text: str) -> str:
    if not text:
        return ""

    cleaned = _clean_pdf_text(text)

    try:
        reshaper = arabic_reshaper.ArabicReshaper(
            {
                "delete_harakat": False,
                "shift_harakat_position": False,
                "support_ligatures": True,
            }
        )
        reshaped = reshaper.reshape(cleaned)
        return get_display(reshaped)
    except Exception:
        return cleaned

# Define a function to measure the width of a given text string when rendered with a specific font. It uses the textbbox method of the ImageDraw object to calculate the bounding box of the text and returns the width by subtracting the left coordinate from the right coordinate. This function is used to determine how much horizontal space a piece of text will occupy in the PDF, which is essential for proper text wrapping and layout.
def _measure_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
) -> int:
    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font,
    )

    return bbox[2] - bbox[0]

# Define a function to calculate the width of a given text string when rendered with a specific font, taking into account the shaping of Arabic text. It first shapes the input text using the _shape_arabic function and then measures the width of the shaped text using the _measure_text function. This function is crucial for accurately determining the space required for Arabic text in the PDF, ensuring that it is properly wrapped and aligned within the layout.
def _text_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
) -> int:
    shaped = _shape_arabic(text)
    return _measure_text(draw, shaped, font)

# Define a function to wrap Arabic text into multiple lines based on a specified maximum width. It takes an ImageDraw object, the input text, the font to be used for rendering, and the maximum width for each line. The function splits the input text into words and iteratively builds lines by adding words until the line exceeds the maximum width. If a single word exceeds the maximum width, it further breaks it down into characters. The resulting list of lines is returned, which can then be rendered in the PDF with proper wrapping.
def _wrap_rtl_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
):
    words = _clean_pdf_text(text).split()

    if not words:
        return []

    lines = []
    current = ""
    
    # Iterate through the words and build lines by adding words until the line exceeds the maximum width. If a single word exceeds the maximum width, break it down into characters to ensure it fits within the layout constraints of the PDF.
    for word in words:
        trial = word if not current else f"{current} {word}"

        if _text_width(draw, trial, font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)

            if _text_width(draw, word, font) <= max_width:
                current = word
            else:
                # Fallback for very long words: split by characters.
                chunk = ""
                for char in word:
                    trial_chunk = chunk + char
                    if _text_width(draw, trial_chunk, font) <= max_width:
                        chunk = trial_chunk
                    else:
                        if chunk:
                            lines.append(chunk)
                        chunk = char
                current = chunk

    if current:
        lines.append(current)

    return lines

# Define a function to resolve an image from a given URL or file path. It checks if the URL is a media URL and attempts to load the image from the media directory. If the URL is an HTTP or HTTPS URL, it makes a request to fetch the image content and loads it into a PIL Image object. If the URL is a local file path, it tries to load the image directly from the filesystem. The function returns the loaded image as a PIL Image object or None if the image cannot be resolved or loaded.
def _resolve_image(url: str):
    url = (url or "").strip()

    # If the URL is empty after stripping whitespace, return None to indicate that there is no image to resolve. This check prevents unnecessary processing and potential errors when attempting to load an image from an empty or invalid URL.
    if not url:
        return None
    
    # Handle media URLs by resolving the relative path to the media root and attempting to load the image from the filesystem. This allows for efficient access to images that have been uploaded and stored in the media directory of the application. If the image file exists, it is loaded and returned as a PIL Image object; otherwise, None is returned.
    if url.startswith(settings.MEDIA_URL):
        rel = url.replace(settings.MEDIA_URL, "", 1)
        path = Path(settings.MEDIA_ROOT) / rel

        try:
            return Image.open(path).convert("RGB") if path.exists() else None
        except Exception:
            return None

    # Handle absolute URLs (http:// or https://) by making an HTTP request to fetch the image content. If the request is successful and the content is a valid image, it loads the image into a PIL Image object and returns it. If any step in this process fails, such as a network error or invalid image content, it returns None.
    if url.startswith("http://") or url.startswith("https://"):
        try:
            res = httpx.get(url, timeout=60)
            res.raise_for_status()
            return Image.open(io.BytesIO(res.content)).convert("RGB")
        except Exception:
            return None

    candidate = Path(url)

    try:
        if candidate.exists():
            return Image.open(candidate).convert("RGB")
    except Exception:
        return None

    return None

# Define a function to fit an image within specified maximum width and height constraints while maintaining its aspect ratio. It creates a copy of the input image and uses the thumbnail method to resize it in place, ensuring that the resulting image does not exceed the given dimensions. The fitted image is then returned as a new PIL Image object, which can be used for rendering in the PDF without distortion.
def _fit_image(img: Image.Image, max_w: int, max_h: int):
    copy = img.copy()
    copy.thumbnail((max_w, max_h))
    return copy

# Define a function to draw right-to-left (RTL) text on an ImageDraw canvas. It takes the drawing context, the position to start drawing, the input text, the font to be used, the fill color, and an optional anchor parameter to specify text alignment. The function shapes the input text for Arabic script using the _shape_arabic function and then draws it on the canvas according to the specified anchor alignment (right-aligned or center-aligned). This function ensures that RTL text is rendered correctly in the PDF, taking into account the unique characteristics of Arabic script.
def _draw_rtl_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font,
    fill,
    anchor: str = "ra",
):
    x, y = xy
    shaped = _shape_arabic(text)

    bbox = draw.textbbox((0, 0), shaped, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    if anchor == "mm":
        draw.text(
            (x - (text_w / 2), y - (text_h / 2)),
            shaped,
            font=font,
            fill=fill,
        )
        return

    if anchor == "ra":
        draw.text(
            (x - text_w, y),
            shaped,
            font=font,
            fill=fill,
        )
        return

    draw.text(
        xy,
        shaped,
        font=font,
        fill=fill,
    )

# Define a function to safely update the PDF generation progress for a story. It takes the story object, the new progress value as an integer, and an optional error message. The function attempts to update the story's pdf_progress field with the new value, ensuring that it stays within the range of 0 to 100. If an error message is provided, it also updates the pdf_error field of the story. The function uses a try-except block to handle any exceptions that may occur during the update process, preventing crashes and ensuring that the application remains stable even if there are issues with updating the database.
def _safe_update_pdf_progress(story, value: int, error: str = ""):
    try:
        story.pdf_progress = max(0, min(100, int(value)))

        if error:
            story.pdf_error = error

        update_fields = ["pdf_progress"]

        if error:
            update_fields.append("pdf_error")

        story.save(update_fields=update_fields)
    except Exception:
        pass

# Define a function to draw the cover page of a story. It creates a new canvas with the specified page dimensions and background color, then draws a rounded rectangle as the card background. It attempts to resolve and fit the cover image if available, and pastes it onto the canvas. The function also draws the story title, child name, and a footer text using appropriate fonts and colors. The resulting cover page is returned as a PIL Image object, which can be included as the first page of the generated PDF.
def _draw_cover(story):
    canvas = Image.new("RGB", (PAGE_W, PAGE_H), BOOK_BG)
    draw = ImageDraw.Draw(canvas)

    outer = [MARGIN, MARGIN, PAGE_W - MARGIN, PAGE_H - MARGIN]
    draw.rounded_rectangle(outer, radius=36, fill=CARD_BG)

    cover_img = _resolve_image(getattr(story, "cover_url", ""))

    image_box = [
        MARGIN + 60,
        MARGIN + 60,
        PAGE_W - MARGIN - 60,
        PAGE_H - MARGIN - 220,
    ]
    
    # If a cover image is available, it fits the image within the defined image box while maintaining the aspect ratio and pastes it onto the canvas. If no cover image is provided, it draws a rounded rectangle with a specified background color in the area designated for the cover image. This ensures that the cover page has a visually appealing layout regardless of whether a custom cover image is available.
    if cover_img:
        fitted = _fit_image(
            cover_img,
            image_box[2] - image_box[0],
            image_box[3] - image_box[1],
        )

        x = image_box[0] + ((image_box[2] - image_box[0]) - fitted.width) // 2
        y = image_box[1] + ((image_box[3] - image_box[1]) - fitted.height) // 2

        canvas.paste(fitted, (x, y))
    else:
        draw.rounded_rectangle(image_box, radius=28, fill=IMAGE_BG)

    title_font = _font(FONT_BOLD_PATH, 54)
    child_font = _font(FONT_PATH, 34)
    footer_font = _font(FONT_PATH, 26)

    _draw_rtl_text(
        draw,
        (PAGE_W - MARGIN - 80, PAGE_H - 170),
        story.title or "قصة",
        font=title_font,
        fill=TEXT_COLOR,
        anchor="ra",
    )

    _draw_rtl_text(
        draw,
        (PAGE_W - MARGIN - 80, PAGE_H - 110),
        f"قصة {story.child.name}",
        font=child_font,
        fill=MUTED_COLOR,
        anchor="ra",
    )

    _draw_rtl_text(
        draw,
        (MARGIN + 160, PAGE_H - 80),
        "غِراس",
        font=footer_font,
        fill=MUTED_COLOR,
        anchor="ra",
    )

    return canvas

# Define a function to draw an individual story page. It creates a new canvas with the specified page dimensions and background color, then draws a rounded rectangle as the card background. The function determines the layout of the image and text panels based on the page index (odd or even) to create a visually dynamic design. It attempts to resolve and fit the illustration image if available, and pastes it onto the canvas. The narration text is wrapped and drawn in the text panel using appropriate fonts and colors. Finally, it adds a footer text indicating the current page number and total pages. The resulting story page is returned as a PIL Image object, which can be included in the generated PDF.
def _draw_story_page(story, page, page_idx: int, total_pages: int):
    canvas = Image.new("RGB", (PAGE_W, PAGE_H), BOOK_BG)
    draw = ImageDraw.Draw(canvas)

    draw.rounded_rectangle(
        [MARGIN, MARGIN, PAGE_W - MARGIN, PAGE_H - MARGIN],
        radius=36,
        fill=CARD_BG,
    )

    image_first = page_idx % 2 == 1

    image_x = (
        MARGIN + 40
        if image_first
        else PAGE_W - MARGIN - 40 - IMAGE_PANEL_W
    )

    text_x = (
        PAGE_W - MARGIN - 40 - TEXT_PANEL_W
        if image_first
        else MARGIN + 40
    )

    image_rect = [
        image_x,
        MARGIN + 40,
        image_x + IMAGE_PANEL_W,
        PAGE_H - MARGIN - 40,
    ]

    text_rect = [
        text_x,
        MARGIN + 40,
        text_x + TEXT_PANEL_W,
        PAGE_H - MARGIN - 40,
    ]

    draw.rounded_rectangle(text_rect, radius=28, fill=TEXT_BG)
    draw.rounded_rectangle(image_rect, radius=28, fill=IMAGE_BG)

    img = _resolve_image(getattr(page, "illustration_url", ""))

    # If an illustration image is available for the story page, it fits the image within the defined image panel while maintaining the aspect ratio and pastes it onto the canvas. This ensures that the illustration is displayed prominently on the page without distortion, enhancing the visual appeal of the story page in the generated PDF.
    if img:
        fitted = _fit_image(
            img,
            IMAGE_PANEL_W - 40,
            image_rect[3] - image_rect[1] - 40,
        )

        x = image_rect[0] + (IMAGE_PANEL_W - fitted.width) // 2
        y = image_rect[1] + ((image_rect[3] - image_rect[1]) - fitted.height) // 2

        canvas.paste(fitted, (x, y))

    text_font = _font(FONT_PATH, 38)
    page_font = _font(FONT_PATH, 24)

    text_area_w = TEXT_PANEL_W - 90

    lines = _wrap_rtl_text(
        draw,
        getattr(page, "narration_text", ""),
        text_font,
        text_area_w,
    )

    line_h = 64
    block_h = len(lines) * line_h

    start_y = text_rect[1] + max(
        80,
        ((text_rect[3] - text_rect[1]) - block_h) // 2,
    )

    for idx, line in enumerate(lines):
        _draw_rtl_text(
            draw,
            (text_rect[2] - 45, start_y + idx * line_h),
            line,
            font=text_font,
            fill=TEXT_COLOR,
            anchor="ra",
        )

    _draw_rtl_text(
        draw,
        (text_rect[0] + (TEXT_PANEL_W // 2), text_rect[3] - 36),
        f"صفحة {page_idx} من {total_pages}",
        font=page_font,
        fill=MUTED_COLOR,
        anchor="mm",
    )

    return canvas

# Define a function to build the PDF bytes for a given story. It prepares the cover page and iterates through the story pages to draw each page, collecting the resulting images in a list. The function uses an optional progress_callback to provide updates on the PDF generation progress. After all pages are prepared, it combines them into a single PDF file using the save method of the first image, and returns the PDF content as bytes. This function is central to the PDF generation process, orchestrating the creation of each page and handling the assembly of the final PDF document.
def build_story_pdf_bytes(story, progress_callback=None):
    images = []

    if progress_callback:
        progress_callback(5, "Preparing PDF cover page")

    images.append(_draw_cover(story))

    if progress_callback:
        progress_callback(10, "Cover page prepared")

    pages = list(story.pages.all().order_by("page_number"))
    total_pages = len(pages)

    for idx, page in enumerate(pages, start=1):
        if progress_callback:
            progress = 10 + int(((idx - 1) / max(total_pages, 1)) * 75)
            progress_callback(progress, f"Preparing PDF page {idx} of {total_pages}")

        images.append(_draw_story_page(story, page, idx, total_pages))

        if progress_callback and total_pages:
            progress = 10 + int((idx / total_pages) * 75)
            progress_callback(min(progress, 85), f"PDF page {idx} prepared")

    if not images:
        images = [Image.new("RGB", (PAGE_W, PAGE_H), "white")]

    buffer = io.BytesIO()

    if progress_callback:
        progress_callback(90, "Combining PDF pages")

    images[0].save(
        buffer,
        format="PDF",
        save_all=True,
        append_images=images[1:],
    )

    if progress_callback:
        progress_callback(95, "Saving PDF file")

    buffer.seek(0)

    return buffer.getvalue()

# Define a function to save the generated PDF for a story. It updates the story's PDF generation status and progress, then calls the build_story_pdf_bytes function to generate the PDF content. The resulting PDF bytes are saved to the story's pdf_file field, and the story's status is updated to indicate that the PDF is ready. If any errors occur during this process, it updates the story's status to indicate failure and saves the error message. This function ensures that the PDF generation process is tracked and that any issues are properly handled and recorded in the story's metadata.
def save_story_pdf(story):
    try:
        story.pdf_status = "generating"
        story.pdf_progress = 1
        story.pdf_error = ""
        story.save(update_fields=["pdf_status", "pdf_progress", "pdf_error"])

        def update_progress(value: int, message: str = ""):
            _safe_update_pdf_progress(story, value, message)

        pdf_bytes = build_story_pdf_bytes(
            story,
            progress_callback=update_progress,
        )

        filename = f"story_{story.id}.pdf"

        story.pdf_file.save(
            filename,
            ContentFile(pdf_bytes),
            save=False,
        )

        story.pdf_status = "ready"
        story.pdf_progress = 100
        story.pdf_error = ""
        story.save(
            update_fields=[
                "pdf_file",
                "pdf_status",
                "pdf_progress",
                "pdf_error",
            ]
        )

        return story.pdf_file.url

    # If any exception occurs during the PDF generation or saving process, it catches the exception, updates the story's PDF status to "failed", resets the progress to 0, and saves the error message in the story's metadata. This ensures that any issues are properly recorded and that the application can handle failures gracefully without crashing.
    except Exception as e:
        story.pdf_status = "failed"
        story.pdf_progress = 0
        story.pdf_error = str(e)
        story.save(update_fields=["pdf_status", "pdf_progress", "pdf_error"])
        raise