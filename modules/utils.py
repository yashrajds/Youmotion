import re

def extract_youtube_id(url):
    """
    Extract YouTube video ID from various URL formats
    """
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})'
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None

def format_youtube_embed_url(video_id):
    """
    Format YouTube video ID into embed URL
    """
    return f"https://www.youtube.com/embed/{video_id}"

def validate_youtube_url(url):
    """
    Validate if URL is a valid YouTube URL
    """
    return extract_youtube_id(url) is not None
