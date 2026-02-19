"""
DocMind Studio — Utilities
YouTube URL validation, transcript extraction, text processing

Supports BOTH youtube-transcript-api versions:
  - Old (<1.0): YouTubeTranscriptApi.get_transcript(video_id)
  - New (>=1.0): YouTubeTranscriptApi().fetch(video_id) or FetchedTranscript
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


def _parse_entries(transcript_data) -> Tuple[list, list]:
    """
    Parse transcript entries into (formatted_lines, raw_lines).
    Handles dict entries (old API) and snippet objects (new API).
    """
    formatted_lines = []
    raw_lines = []

    for entry in transcript_data:
        # New API: snippet objects with .text and .start attributes
        if hasattr(entry, 'text') and hasattr(entry, 'start'):
            text = str(entry.text).strip()
            start = float(entry.start)
        # Old API: plain dicts
        elif isinstance(entry, dict):
            text = str(entry.get('text', '')).strip()
            start = float(entry.get('start', 0))
        else:
            # Last resort: try str conversion
            text = str(entry).strip()
            start = 0.0

        if not text:
            continue

        minutes = int(start // 60)
        seconds = int(start % 60)
        formatted_lines.append(f"[{minutes}:{seconds:02d}] {text}")
        raw_lines.append(text)

    return formatted_lines, raw_lines


def fetch_transcript(video_id: str) -> Tuple[bool, str, str, str]:
    """
    Fetch YouTube transcript — compatible with youtube-transcript-api v0.x AND v1.x+
    Returns: (success, formatted_transcript, raw_transcript, error_message)
    """
    try:
        import youtube_transcript_api as _ytt_module
        from youtube_transcript_api import YouTubeTranscriptApi

        # ── Detect API version ──────────────────────────────────────────────
        # v1.0+ removed class methods; YouTubeTranscriptApi is now instantiated
        is_new_api = not callable(getattr(YouTubeTranscriptApi, 'get_transcript', None))

        transcript_data = None
        last_error = ""

        # ══════════════════════════════════════════
        # NEW API  (youtube-transcript-api >= 1.0)
        # ══════════════════════════════════════════
        if is_new_api:
            ytt = YouTubeTranscriptApi()

            # Strategy 1: fetch() directly — works when captions exist
            try:
                transcript_data = ytt.fetch(video_id, languages=['en', 'en-US', 'en-GB'])
            except Exception as e1:
                last_error = str(e1)

            # Strategy 2: no language filter
            if transcript_data is None:
                try:
                    transcript_data = ytt.fetch(video_id)
                except Exception as e2:
                    last_error = str(e2)

            # Strategy 3: list_transcripts → pick best → fetch
            if transcript_data is None:
                try:
                    tlist = ytt.list_transcripts(video_id)
                    # prefer manual, then auto-generated
                    picked = None
                    for t in tlist:
                        if not t.is_generated:
                            picked = t
                            break
                    if picked is None:
                        for t in tlist:
                            picked = t
                            break
                    if picked:
                        transcript_data = picked.fetch()
                except Exception as e3:
                    last_error = str(e3)

        # ══════════════════════════════════════════
        # OLD API  (youtube-transcript-api < 1.0)
        # ══════════════════════════════════════════
        else:
            # Strategy 1: explicit language list
            try:
                transcript_data = YouTubeTranscriptApi.get_transcript(
                    video_id, languages=['en', 'en-US', 'en-GB', 'a.en']
                )
            except Exception as e1:
                last_error = str(e1)

            # Strategy 2: no language preference
            if transcript_data is None:
                try:
                    transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
                except Exception as e2:
                    last_error = str(e2)

            # Strategy 3: list → pick → fetch
            if transcript_data is None:
                try:
                    tlist = YouTubeTranscriptApi.list_transcripts(video_id)
                    picked = None
                    for t in tlist:
                        if not t.is_generated:
                            picked = t
                            break
                    if picked is None:
                        for t in tlist:
                            picked = t
                            break
                    if picked:
                        transcript_data = picked.fetch()
                except Exception as e3:
                    last_error = str(e3)

        # ── Parse whatever we got ───────────────────────────────────────────
        if not transcript_data:
            return _transcript_error(last_error)

        formatted_lines, raw_lines = _parse_entries(transcript_data)

        if not raw_lines:
            return False, "", "", "Transcript was empty. Please try another video."

        return True, '\n'.join(formatted_lines), ' '.join(raw_lines), ""

    except ImportError:
        return (
            False, "", "",
            "youtube-transcript-api is not installed. Add it to requirements.txt."
        )
    except Exception as e:
        return _transcript_error(str(e))


def _transcript_error(err: str) -> Tuple[bool, str, str, str]:
    """Map raw exception text to a user-friendly error message."""
    e = err.lower()
    if any(k in e for k in ["no transcript", "could not retrieve", "notranscript",
                             "no captions", "subtitles are disabled"]):
        msg = ("No captions found for this video. "
               "Please try a video that has auto-generated or manual captions enabled.")
    elif any(k in e for k in ["disabled", "transcriptsdisabled"]):
        msg = "Captions are disabled for this video. Please try another video."
    elif any(k in e for k in ["unavailable", "private", "not available", "video unavailable"]):
        msg = "This video is private or unavailable. Please check the URL and try again."
    elif "too many requests" in e or "429" in err:
        msg = "YouTube is rate-limiting requests. Please wait a moment and try again."
    elif "ip" in e and ("block" in e or "ban" in e):
        msg = ("YouTube blocked this request (IP restriction on the server). "
               "Try a different video or re-deploy on another host.")
    elif "has no attribute" in e:
        msg = ("youtube-transcript-api version mismatch detected. "
               "Please upgrade: pip install --upgrade youtube-transcript-api")
    else:
        msg = f"Could not fetch transcript. Try a different YouTube video. (Detail: {err[:180]})"
    return False, "", "", msg


# ── Text processing helpers ─────────────────────────────────────────────────

def chunk_transcript(raw_transcript: str, max_words: int = 7000) -> str:
    """Chunk long transcripts to fit within LLM token limits."""
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
    """Extract SEO metadata lines from generated blog content."""
    metadata = {
        "seo_title": "",
        "meta_description": "",
        "primary_keyword": "",
        "secondary_keywords": [],
    }
    for line in blog_content.split('\n'):
        ll = line.lower()
        if ':' not in line:
            continue
        val = re.sub(r'\*+', '', line.split(':', 1)[-1]).strip()
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
    """Strip metadata header lines so only blog body is shown."""
    skip = ['seo title', 'meta description', 'primary keyword', 'secondary keyword']
    lines = [l for l in blog_content.split('\n')
             if not any(k in l.lower() for k in skip)]
    return '\n'.join(lines).strip()


def count_words(text: str) -> int:
    text = re.sub(r'[#*`\[\]()>~_]', '', text)
    return len(text.split())


def format_word_count(count: int) -> str:
    return f"{count / 1000:.1f}k words" if count >= 1000 else f"{count} words"
