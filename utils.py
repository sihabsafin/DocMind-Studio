"""
DocMind Studio — Utilities
YouTube URL validation, transcript extraction, text processing
"""

import re
import time
from typing import Optional, Tuple


def extract_video_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from various URL formats"""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        r'youtube\.com/v/([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def validate_youtube_url(url: str) -> Tuple[bool, str]:
    """
    Validate YouTube URL.
    Returns (is_valid, message)
    """
    if not url.strip():
        return False, ""
    
    video_id = extract_video_id(url)
    if video_id:
        return True, video_id
    return False, "Please enter a valid YouTube URL (youtube.com/watch?v=... or youtu.be/...)"


def fetch_transcript(video_id: str) -> Tuple[bool, str, str]:
    """
    Fetch YouTube transcript.
    Returns (success, transcript_text, error_message)
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
        
        # Try to get transcript - manual first, then auto-generated
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Format transcript with timestamps
        formatted_lines = []
        raw_lines = []
        
        for entry in transcript_list:
            start = entry.get('start', 0)
            text = entry.get('text', '').strip()
            if text:
                minutes = int(start // 60)
                seconds = int(start % 60)
                timestamp = f"[{minutes}:{seconds:02d}]"
                formatted_lines.append(f"{timestamp} {text}")
                raw_lines.append(text)
        
        formatted = '\n'.join(formatted_lines)
        raw = ' '.join(raw_lines)
        
        return True, formatted, raw, ""
        
    except Exception as e:
        err = str(e)
        if "NoTranscriptFound" in err or "Could not retrieve" in err:
            return False, "", "", "This video doesn't have captions enabled. Please try a video with auto-generated or manual captions."
        elif "TranscriptsDisabled" in err:
            return False, "", "", "Transcripts are disabled for this video. Please try another video."
        elif "VideoUnavailable" in err or "private" in err.lower():
            return False, "", "", "This video is private or unavailable. Please check the URL."
        else:
            return False, "", "", f"Could not fetch transcript: {err}"


def fetch_transcript(video_id: str):
    """
    Fetch YouTube transcript.
    Returns (success, formatted_transcript, raw_transcript, error_message)
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
        formatted_lines = []
        raw_lines = []
        
        for entry in transcript_list:
            start = entry.get('start', 0)
            text = entry.get('text', '').strip()
            if text:
                minutes = int(start // 60)
                seconds = int(start % 60)
                timestamp = f"[{minutes}:{seconds:02d}]"
                formatted_lines.append(f"{timestamp} {text}")
                raw_lines.append(text)
        
        formatted = '\n'.join(formatted_lines)
        raw = ' '.join(raw_lines)
        
        return True, formatted, raw, ""
        
    except Exception as e:
        err = str(e)
        if "No transcript" in err or "Could not retrieve" in err:
            return False, "", "", "This video doesn't have captions enabled. Please try a video with auto-generated or manual captions."
        elif "disabled" in err.lower():
            return False, "", "", "Transcripts are disabled for this video. Please try another video."
        elif "unavailable" in err.lower() or "private" in err.lower():
            return False, "", "", "This video is private or unavailable. Please check the URL."
        else:
            return False, "", "", f"Could not fetch transcript. Please try another video."


def chunk_transcript(raw_transcript: str, max_words: int = 8000) -> str:
    """Chunk long transcripts to fit within token limits"""
    words = raw_transcript.split()
    if len(words) <= max_words:
        return raw_transcript
    
    # For very long transcripts, take beginning + middle + end
    chunk_size = max_words // 3
    beginning = ' '.join(words[:chunk_size])
    middle_start = len(words) // 2 - chunk_size // 2
    middle = ' '.join(words[middle_start:middle_start + chunk_size])
    end = ' '.join(words[-chunk_size:])
    
    return f"{beginning}\n\n[...content summarized...]\n\n{middle}\n\n[...content summarized...]\n\n{end}"


def parse_blog_metadata(blog_content: str) -> dict:
    """Extract SEO metadata from blog content"""
    metadata = {
        "seo_title": "",
        "meta_description": "",
        "primary_keyword": "",
        "secondary_keywords": [],
    }
    
    lines = blog_content.split('\n')
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if 'seo title:' in line_lower or '**seo title:**' in line_lower:
            metadata["seo_title"] = re.sub(r'\*\*.*?\*\*\s*', '', line).replace('SEO Title:', '').replace('seo title:', '').strip()
        elif 'meta description:' in line_lower or '**meta description:**' in line_lower:
            metadata["meta_description"] = re.sub(r'\*\*.*?\*\*\s*', '', line).replace('Meta Description:', '').replace('meta description:', '').strip()
        elif 'primary keyword:' in line_lower or '**primary keyword:**' in line_lower:
            metadata["primary_keyword"] = re.sub(r'\*\*.*?\*\*\s*', '', line).replace('Primary Keyword:', '').replace('primary keyword:', '').strip()
        elif 'secondary keyword' in line_lower:
            # Try to extract secondary keywords from next lines or same line
            kw_text = line.split(':', 1)[-1].strip()
            if kw_text:
                metadata["secondary_keywords"] = [k.strip() for k in kw_text.replace('**', '').split(',') if k.strip()]
    
    return metadata


def clean_blog_for_display(blog_content: str) -> str:
    """Remove metadata header lines for clean display of blog body"""
    lines = blog_content.split('\n')
    clean_lines = []
    skip_keywords = ['seo title:', 'meta description:', 'primary keyword:', 'secondary keyword']
    
    for line in lines:
        line_lower = line.lower()
        skip = any(kw in line_lower for kw in skip_keywords)
        if not skip:
            clean_lines.append(line)
    
    return '\n'.join(clean_lines).strip()


def count_words(text: str) -> int:
    """Count words in text, stripping markdown"""
    text = re.sub(r'[#*`\[\]()>]', '', text)
    return len(text.split())


def format_word_count(count: int) -> str:
    """Format word count nicely"""
    if count >= 1000:
        return f"{count/1000:.1f}k words"
    return f"{count} words"
