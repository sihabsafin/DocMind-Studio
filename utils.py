"""
DocMind Studio — Utilities
YouTube URL validation, transcript extraction, text processing

youtube-transcript-api version compatibility:
  v0.x  → YouTubeTranscriptApi.get_transcript(id)       [class method]
  v1.x+ → YouTubeTranscriptApi().fetch(id)               [instance method]
  
Strategy: probe available methods at runtime, never assume.
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
    if not url.strip():
        return False, ""
    video_id = extract_video_id(url)
    if video_id:
        return True, video_id
    return False, "Please enter a valid YouTube URL (youtube.com/watch?v=... or youtu.be/...)"


def _parse_entries(transcript_data) -> Tuple[list, list]:
    """
    Parse transcript entries — handles dict (old API) and object (new API) forms.
    """
    formatted_lines = []
    raw_lines = []
    for entry in transcript_data:
        try:
            if isinstance(entry, dict):
                text = str(entry.get('text', '')).strip()
                start = float(entry.get('start', 0))
            elif hasattr(entry, 'text') and hasattr(entry, 'start'):
                text = str(entry.text).strip()
                start = float(entry.start)
            else:
                # Last resort: try converting to dict
                d = dict(entry)
                text = str(d.get('text', '')).strip()
                start = float(d.get('start', 0))

            if not text:
                continue
            m, s = int(start // 60), int(start % 60)
            formatted_lines.append(f"[{m}:{s:02d}] {text}")
            raw_lines.append(text)
        except Exception:
            continue
    return formatted_lines, raw_lines


def fetch_transcript(video_id: str) -> Tuple[bool, str, str, str]:
    """
    Fetch transcript — works with youtube-transcript-api v0.x AND v1.x+
    Returns: (success, formatted, raw, error_message)
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        # ── Probe which API shape we have ────────────────────────────────────
        # v1.x: class has NO 'get_transcript' or 'list_transcripts' class methods
        #        → must instantiate: ytt = YouTubeTranscriptApi()
        #        → then call: ytt.fetch(video_id)  or  ytt.list(video_id)
        # v0.x: class HAS 'get_transcript' as a callable class/static method
        
        has_class_get = callable(getattr(YouTubeTranscriptApi, 'get_transcript', None))
        
        transcript_data = None
        last_error = ""

        if not has_class_get:
            # ════════════════════════════════════════
            # NEW API  (v1.0+)
            # YouTubeTranscriptApi() must be instantiated
            # Methods: .fetch(video_id, languages=[...])
            #          .list(video_id)  ← NOT list_transcripts
            # ════════════════════════════════════════
            try:
                ytt = YouTubeTranscriptApi()
            except Exception as e:
                return False, "", "", f"Could not initialize YouTubeTranscriptApi: {e}"

            # Probe instance methods
            has_fetch = callable(getattr(ytt, 'fetch', None))
            has_list  = callable(getattr(ytt, 'list', None))
            has_list_transcripts = callable(getattr(ytt, 'list_transcripts', None))

            # Attempt 1: fetch() with language preference
            if has_fetch:
                for lang_args in [
                    {'languages': ['en', 'en-US', 'en-GB']},
                    {},  # no language filter
                ]:
                    try:
                        transcript_data = ytt.fetch(video_id, **lang_args)
                        if transcript_data:
                            break
                    except Exception as e:
                        last_error = str(e)

            # Attempt 2: list() → pick best → fetch()
            if transcript_data is None:
                list_fn = None
                if has_list:
                    list_fn = ytt.list
                elif has_list_transcripts:
                    list_fn = ytt.list_transcripts

                if list_fn:
                    try:
                        tlist = list(list_fn(video_id))
                        picked = None
                        # Prefer manual over auto-generated
                        for t in tlist:
                            if hasattr(t, 'is_generated') and not t.is_generated:
                                picked = t
                                break
                        if picked is None and tlist:
                            picked = tlist[0]
                        if picked is not None:
                            transcript_data = picked.fetch()
                    except Exception as e:
                        last_error = str(e)

        else:
            # ════════════════════════════════════════
            # OLD API  (v0.x)
            # YouTubeTranscriptApi.get_transcript() is a class method
            # ════════════════════════════════════════

            # Attempt 1: with language preference
            try:
                transcript_data = YouTubeTranscriptApi.get_transcript(
                    video_id, languages=['en', 'en-US', 'en-GB', 'a.en']
                )
            except Exception as e:
                last_error = str(e)

            # Attempt 2: no language filter
            if transcript_data is None:
                try:
                    transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
                except Exception as e:
                    last_error = str(e)

            # Attempt 3: list_transcripts → pick best
            if transcript_data is None:
                try:
                    tlist = list(YouTubeTranscriptApi.list_transcripts(video_id))
                    picked = None
                    for t in tlist:
                        if hasattr(t, 'is_generated') and not t.is_generated:
                            picked = t
                            break
                    if picked is None and tlist:
                        picked = tlist[0]
                    if picked is not None:
                        transcript_data = picked.fetch()
                except Exception as e:
                    last_error = str(e)

        # ── Parse result ──────────────────────────────────────────────────────
        if not transcript_data:
            return _transcript_error(last_error or "No transcript data returned")

        formatted_lines, raw_lines = _parse_entries(transcript_data)

        if not raw_lines:
            return False, "", "", "Transcript appears to be empty. Please try another video."

        return True, '\n'.join(formatted_lines), ' '.join(raw_lines), ""

    except ImportError:
        return False, "", "", "youtube-transcript-api is not installed. Check requirements.txt."
    except Exception as e:
        return _transcript_error(str(e))


def _transcript_error(err: str) -> Tuple[bool, str, str, str]:
    """Convert raw exception message to a user-friendly string."""
    e = err.lower()
    if any(k in e for k in [
        "no transcript", "could not retrieve", "notranscript",
        "no captions", "subtitles are disabled", "transcript list"
    ]):
        msg = (
            "No captions found for this video. "
            "Please try a video with auto-generated or manual captions enabled."
        )
    elif "disabled" in e or "transcriptsdisabled" in e:
        msg = "Captions are disabled for this video. Please try another video."
    elif any(k in e for k in ["unavailable", "private", "not available", "video unavailable"]):
        msg = "This video is private or unavailable. Please check the URL."
    elif "too many requests" in e or "429" in err:
        msg = "YouTube is rate-limiting requests. Please wait a moment and try again."
    elif "ip" in e and ("block" in e or "ban" in e):
        msg = "YouTube blocked this server's IP. Try a different video or re-deploy."
    else:
        msg = f"Could not fetch transcript. Try a different YouTube video. (Detail: {err[:200]})"
    return False, "", "", msg


# ── Text helpers ──────────────────────────────────────────────────────────────

def chunk_transcript(raw_transcript: str, max_words: int = 7000) -> str:
    words = raw_transcript.split()
    if len(words) <= max_words:
        return raw_transcript
    chunk = max_words // 3
    beg = ' '.join(words[:chunk])
    mid_s = len(words) // 2 - chunk // 2
    mid = ' '.join(words[mid_s:mid_s + chunk])
    end = ' '.join(words[-chunk:])
    return f"{beg}\n\n[...middle summarized...]\n\n{mid}\n\n[...end summarized...]\n\n{end}"


def parse_blog_metadata(blog_content: str) -> dict:
    meta = {"seo_title": "", "meta_description": "", "primary_keyword": "", "secondary_keywords": []}
    for line in blog_content.split('\n'):
        ll = line.lower()
        if ':' not in line:
            continue
        val = re.sub(r'\*+', '', line.split(':', 1)[-1]).strip()
        if not val:
            continue
        if 'seo title' in ll:
            meta["seo_title"] = val
        elif 'meta description' in ll:
            meta["meta_description"] = val
        elif 'primary keyword' in ll:
            meta["primary_keyword"] = val
        elif 'secondary keyword' in ll:
            meta["secondary_keywords"] = [k.strip() for k in val.split(',') if k.strip()]
    return meta


def clean_blog_for_display(blog_content: str) -> str:
    skip = ['seo title', 'meta description', 'primary keyword', 'secondary keyword']
    return '\n'.join(
        l for l in blog_content.split('\n')
        if not any(k in l.lower() for k in skip)
    ).strip()


def count_words(text: str) -> int:
    return len(re.sub(r'[#*`\[\]()>~_]', '', text).split())


def format_word_count(count: int) -> str:
    return f"{count / 1000:.1f}k words" if count >= 1000 else f"{count} words"
