"""
DocMind Studio — Utilities
YouTube URL validation, transcript extraction, text processing

youtube-transcript-api version compatibility:
  v0.x  → YouTubeTranscriptApi.get_transcript(id)       [class method]
  v1.x+ → YouTubeTranscriptApi().fetch(id)               [instance method]

Strategy: probe available methods at runtime, never assume.
"""

import os
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
                try:
                    d = dict(entry)
                    text = str(d.get('text', '')).strip()
                    start = float(d.get('start', 0))
                except Exception:
                    continue

            if not text:
                continue
            m, s = int(start // 60), int(start % 60)
            formatted_lines.append(f"[{m}:{s:02d}] {text}")
            raw_lines.append(text)
        except Exception:
            continue
    return formatted_lines, raw_lines


def _build_ytt_instance():
    """
    Build a YouTubeTranscriptApi instance.
    If WEBSHARE_USERNAME + WEBSHARE_PASSWORD are set in env/secrets,
    uses Webshare rotating residential proxies (required for cloud deployments).
    Otherwise falls back to direct connection (works locally).
    """
    from youtube_transcript_api import YouTubeTranscriptApi

    proxy_user = os.environ.get("WEBSHARE_USERNAME", "")
    proxy_pass = os.environ.get("WEBSHARE_PASSWORD", "")

    # Try Streamlit secrets too
    if not proxy_user:
        try:
            import streamlit as st
            proxy_user = st.secrets.get("WEBSHARE_USERNAME", "")
            proxy_pass = st.secrets.get("WEBSHARE_PASSWORD", "")
        except Exception:
            pass

    if proxy_user and proxy_pass:
        try:
            from youtube_transcript_api.proxies import WebshareProxyConfig
            return YouTubeTranscriptApi(
                proxy_config=WebshareProxyConfig(
                    proxy_username=proxy_user,
                    proxy_password=proxy_pass,
                )
            ), True  # (instance, using_proxy)
        except ImportError:
            pass  # older version, fall through to direct

    return YouTubeTranscriptApi(), False


def fetch_transcript(video_id: str) -> Tuple[bool, str, str, str]:
    """
    Fetch transcript — works with youtube-transcript-api v0.x AND v1.x+
    Supports Webshare proxy for cloud deployments (set WEBSHARE_USERNAME + WEBSHARE_PASSWORD).
    Returns: (success, formatted, raw, error_message)
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        # ── Detect API version ───────────────────────────────────────────────
        # v0.x: get_transcript is a callable class/static method
        # v1.x: must instantiate — get_transcript doesn't exist as class method
        has_class_get = callable(getattr(YouTubeTranscriptApi, 'get_transcript', None))

        transcript_data = None
        last_error = ""
        using_proxy = False

        # ════════════════════════════════════════════════
        # NEW API  (v1.0+)  — instantiate, then .fetch()
        # ════════════════════════════════════════════════
        if not has_class_get:
            try:
                ytt, using_proxy = _build_ytt_instance()
            except Exception as e:
                return False, "", "", f"Could not initialize YouTubeTranscriptApi: {e}"

            has_fetch            = callable(getattr(ytt, 'fetch', None))
            has_list             = callable(getattr(ytt, 'list', None))
            has_list_transcripts = callable(getattr(ytt, 'list_transcripts', None))

            if has_fetch:
                for lang_args in [{'languages': ['en', 'en-US', 'en-GB']}, {}]:
                    try:
                        transcript_data = ytt.fetch(video_id, **lang_args)
                        if transcript_data:
                            break
                    except Exception as e:
                        last_error = str(e)

            if transcript_data is None:
                list_fn = (ytt.list if has_list
                           else ytt.list_transcripts if has_list_transcripts
                           else None)
                if list_fn:
                    try:
                        tlist = list(list_fn(video_id))
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

        # ════════════════════════════════════════════════
        # OLD API  (v0.x)  — class methods
        # ════════════════════════════════════════════════
        else:
            try:
                transcript_data = YouTubeTranscriptApi.get_transcript(
                    video_id, languages=['en', 'en-US', 'en-GB', 'a.en']
                )
            except Exception as e:
                last_error = str(e)

            if transcript_data is None:
                try:
                    transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
                except Exception as e:
                    last_error = str(e)

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
    """Convert raw exception message to a user-friendly error with actionable advice."""
    e = err.lower()

    if any(k in e for k in [
        "no transcript", "could not retrieve", "notranscript",
        "no captions", "subtitles are disabled", "transcript list",
        "no element", "could not find"
    ]):
        msg = (
            "⚠️ This video has no captions available.\n\n"
            "YouTube requires a video to have either auto-generated or manual captions "
            "for transcript extraction to work.\n\n"
            "✅ Try videos from these types of channels — they almost always have captions:\n"
            "• Tech tutorials (e.g. Fireship, Traversy Media, NetworkChuck)\n"
            "• Educational (e.g. Khan Academy, Kurzgesagt, TED)\n"
            "• Business/AI (e.g. Y Combinator, Lex Fridman, MKBHD)\n\n"
            "💡 Tip: Open the video on YouTube → click CC button. "
            "If it's greyed out, the video has no captions."
        )
    elif "disabled" in e or "transcriptsdisabled" in e:
        msg = (
            "⚠️ The video owner has disabled captions for this video.\n\n"
            "Please try a different video. Most educational and tech videos have captions enabled."
        )
    elif any(k in e for k in ["unavailable", "private", "not available", "video unavailable"]):
        msg = (
            "⚠️ This video is private or unavailable.\n\n"
            "Please check the URL and make sure the video is publicly accessible."
        )
    elif "too many requests" in e or "429" in err:
        msg = (
            "⚠️ YouTube is rate-limiting requests. "
            "Please wait 30–60 seconds and try again."
        )
    elif any(k in e for k in ["ip", "request", "blocked", "requestblocked", "ipblocked"]):
        msg = (
            "YouTube is blocking transcript requests from this server's IP address.\n\n"
            "This is a known limitation with ALL cloud platforms — Streamlit Cloud, AWS, GCP, Azure. "
            "YouTube blocks their entire IP ranges at the network level.\n\n"
            "Fix 1 — Run locally (free, works immediately):\n"
            "  streamlit run app.py on your own machine bypasses this entirely.\n\n"
            "Fix 2 — Add a Webshare residential proxy (for cloud deployment):\n"
            "  1. Sign up at webshare.io and purchase a Residential proxy plan (~$3/mo)\n"
            "  2. Add to .streamlit/secrets.toml:\n"
            "     WEBSHARE_USERNAME = \'your-username\'\n"
            "     WEBSHARE_PASSWORD = \'your-password\'\n"
            "  3. Redeploy — DocMind detects the credentials and routes all transcript "
            "requests through Webshare automatically."
        )
    else:
        msg = (
            f"⚠️ Could not fetch transcript.\n\n"
            f"Please try a different YouTube video. Most educational, tech, and tutorial "
            f"videos work well.\n\nDetail: {err[:200]}"
        )
    return False, "", "", msg


# ── Text helpers ─────────────────────────────────────────────────────────────

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
    meta = {
        "seo_title": "", "meta_description": "",
        "primary_keyword": "", "secondary_keywords": []
    }
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
