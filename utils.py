"""
DocMind Studio — Utilities
YouTube URL validation, transcript extraction, text processing
"""

import re
from typing import Optional, Tuple


def extract_video_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from various URL formats"""
    patterns = [
        r'(?:youtube\.com/watch\?v=)([a-zA-Z0-9_-]{11})',
        r'(?:youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com/v/)([a-zA-Z0-9_-]{11})',
    ]
    url = url.strip()
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def validate_youtube_url(url: str) -> Tuple[bool, str]:
    """
    Validate YouTube URL.
    Returns (is_valid, video_id_or_error_message)
    """
    if not url.strip():
        return False, ""

    video_id = extract_video_id(url)
    if video_id:
        return True, video_id
    return False, "Please enter a valid YouTube URL (youtube.com/watch?v=... or youtu.be/...)"


def fetch_transcript(video_id: str) -> Tuple[bool, str, str, str]:
    """
    Fetch YouTube transcript with multiple fallback strategies.
    Returns (success, formatted_transcript, raw_transcript, error_message)
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        transcript_data = None
        error_detail = ""

        # Strategy 1: list all available transcripts and pick best one
        try:
            transcript_list_obj = YouTubeTranscriptApi.list_transcripts(video_id)

            # Try manual English first
            try:
                t = transcript_list_obj.find_manually_created_transcript(['en', 'en-US', 'en-GB'])
                transcript_data = t.fetch()
            except Exception:
                pass

            # Try any manual transcript
            if transcript_data is None:
                try:
                    for t in transcript_list_obj:
                        if not t.is_generated:
                            transcript_data = t.fetch()
                            break
                except Exception:
                    pass

            # Try auto-generated English
            if transcript_data is None:
                try:
                    t = transcript_list_obj.find_generated_transcript(['en', 'en-US', 'en-GB', 'a.en'])
                    transcript_data = t.fetch()
                except Exception:
                    pass

            # Last resort: any available transcript
            if transcript_data is None:
                try:
                    for t in transcript_list_obj:
                        transcript_data = t.fetch()
                        break
                except Exception:
                    pass

        except Exception as list_err:
            error_detail = str(list_err)

        # Strategy 2: direct get_transcript fallback
        if transcript_data is None:
            try:
                transcript_data = YouTubeTranscriptApi.get_transcript(
                    video_id,
                    languages=['en', 'en-US', 'en-GB', 'a.en'],
                )
            except Exception:
                pass

        if transcript_data is None:
            try:
                transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
            except Exception as e:
                error_detail = str(e)

        if not transcript_data:
            return _transcript_error(error_detail)

        # Parse transcript entries (handles both dict and object forms)
        formatted_lines = []
        raw_lines = []

        for entry in transcript_data:
            if hasattr(entry, 'text'):
                text = str(entry.text).strip()
                start = float(getattr(entry, 'start', 0))
            elif isinstance(entry, dict):
                text = str(entry.get('text', '')).strip()
                start = float(entry.get('start', 0))
            else:
                continue

            if not text:
                continue

            minutes = int(start // 60)
            seconds = int(start % 60)
            timestamp = f"[{minutes}:{seconds:02d}]"
            formatted_lines.append(f"{timestamp} {text}")
            raw_lines.append(text)

        if not raw_lines:
            return False, "", "", "Transcript was empty. Please try another video."

        return True, '\n'.join(formatted_lines), ' '.join(raw_lines), ""

    except ImportError:
        return False, "", "", "youtube-transcript-api not installed. Run: pip install youtube-transcript-api"
    except Exception as e:
        return _transcript_error(str(e))


def _transcript_error(err: str) -> Tuple[bool, str, str, str]:
    """Map raw exception text to a friendly error message."""
    e = err.lower()
    if any(k in e for k in ["no transcript", "could not retrieve", "notranscript", "no captions"]):
        msg = "No captions found for this video. Please try a video that has auto-generated or manual captions enabled."
    elif any(k in e for k in ["disabled", "transcriptsdisabled"]):
        msg = "Captions are disabled for this video. Please try another video."
    elif any(k in e for k in ["unavailable", "private", "not available"]):
        msg = "This video is private or unavailable. Please check the URL and try again."
    elif "too many requests" in e or "429" in err:
        msg = "YouTube is rate-limiting requests. Please wait a moment and try again."
    elif "ip" in e and ("block" in e or "ban" in e):
        msg = "YouTube blocked this request (IP restriction on the server). Try a different video or re-deploy."
    else:
        msg = f"Could not fetch transcript. Try a different YouTube video. ({err[:150]})"
    return False, "", "", msg


def chunk_transcript(raw_transcript: str, max_words: int = 7000) -> str:
    """Chunk long transcripts to fit within LLM token limits"""
    words = raw_transcript.split()
    if len(words) <= max_words:
        return raw_transcript

    chunk_size = max_words // 3
    beginning = ' '.join(words[:chunk_size])
    mid_start = len(words) // 2 - chunk_size // 2
    middle = ' '.join(words[mid_start:mid_start + chunk_size])
    end = ' '.join(words[-chunk_size:])

    return (
        f"{beginning}\n\n[...middle content summarized...]\n\n"
        f"{middle}\n\n[...end content summarized...]\n\n{end}"
    )


def parse_blog_metadata(blog_content: str) -> dict:
    """Extract SEO metadata lines from generated blog content"""
    metadata = {
        "seo_title": "",
        "meta_description": "",
        "primary_keyword": "",
        "secondary_keywords": [],
    }

    for line in blog_content.split('\n'):
        ll = line.lower()
        val = re.sub(r'\*+', '', line.split(':', 1)[-1]).strip() if ':' in line else ''
        if not val:
            continue
        if 'seo title' in ll:
            metadata["seo_title"] = val
        elif 'meta description' in ll:
            metadata["meta_description"] = val
        elif 'primary keyword' in ll:
            metadata["primary_keyword"] = val
        elif 'secondary keyword' in ll:
            metadata["secondary_keywords"] = [k.strip() for k in val.split(',') if k.strip()]

    return metadata


def clean_blog_for_display(blog_content: str) -> str:
    """Strip metadata header lines so only blog body is shown"""
    skip = ['seo title', 'meta description', 'primary keyword', 'secondary keyword']
    lines = [l for l in blog_content.split('\n') if not any(k in l.lower() for k in skip)]
    return '\n'.join(lines).strip()


def count_words(text: str) -> int:
    text = re.sub(r'[#*`\[\]()>~_]', '', text)
    return len(text.split())


def format_word_count(count: int) -> str:
    return f"{count / 1000:.1f}k words" if count >= 1000 else f"{count} words"
