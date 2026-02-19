"""
DocMind Studio — Main Application
YouTube to Blog Automation Platform
Built with Streamlit + CrewAI + Groq
"""

import streamlit as st
import time
import re
import os
import markdown as md

st.set_page_config(
    page_title="DocMind Studio",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

from styles import (
    FONTS_AND_STYLES,
    get_stage_bar_html,
    get_agent_card_html,
    get_seo_section_html,
)
from utils import (
    validate_youtube_url,
    fetch_transcript,
    chunk_transcript,
    parse_blog_metadata,
    clean_blog_for_display,
    count_words,
    format_word_count,
)

st.markdown(FONTS_AND_STYLES, unsafe_allow_html=True)

# ── Resolve API key from secrets / env only (never from UI) ─────────────────
def get_groq_api_key() -> str:
    try:
        key = st.secrets.get("GROQ_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("GROQ_API_KEY", "")

GROQ_API_KEY = get_groq_api_key()

# ── Session state ────────────────────────────────────────────────────────────
def init_session_state():
    defaults = {
        "stage": "input",
        "url": "",
        "video_id": None,
        "transcript_formatted": "",
        "transcript_raw": "",
        "blog_content": "",
        "seo_metadata": {},
        "agent_statuses": {
            "Research Analyst":   {"status": "pending", "duration": 0},
            "Content Strategist": {"status": "pending", "duration": 0},
            "SEO Optimizer":      {"status": "pending", "duration": 0},
            "Blog Writer":        {"status": "pending", "duration": 0},
            "Quality Reviewer":   {"status": "pending", "duration": 0},
        },
        "error": None,
        "generation_time": 0,
        "tone": "Professional",
        "length_label": "Medium (~1500 words)",
        "advanced_seo": False,
        "seo_mode": "Basic",
        "word_count_target": 1500,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_state()

# ── TOP BAR ──────────────────────────────────────────────────────────────────
api_dot = "#10b981" if GROQ_API_KEY else "#f43f5e"
api_label = "API Ready" if GROQ_API_KEY else "No API Key"

st.markdown(f"""
<div class="docmind-topbar">
  <div class="docmind-logo">
    <div class="docmind-logo-icon">◈</div>
    <span class="docmind-logo-text">DocMind Studio</span>
  </div>
  <div style="display:flex;align-items:center;gap:10px;">
    <div class="docmind-status-pill">
      <span style="color:{api_dot};font-size:8px;">●</span> {api_label}
    </div>
    <div class="docmind-status-pill">⚡ Groq · Llama 3.3 70B</div>
  </div>
</div>
""", unsafe_allow_html=True)

# Missing API key banner
if not GROQ_API_KEY:
    st.markdown("""
<div style="background:rgba(244,63,94,0.1);border:1px solid rgba(244,63,94,0.4);
     border-radius:10px;padding:14px 20px;margin-bottom:16px;">
  <strong style="color:#f1f5f9;">🔑 Groq API Key Required</strong><br>
  <span style="font-size:13px;color:#cbd5e1;">
    Add <code>GROQ_API_KEY = "gsk_..."</code> to <strong>.streamlit/secrets.toml</strong>.
    Get a free key at <strong>console.groq.com</strong>.
  </span>
</div>
""", unsafe_allow_html=True)

# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:

    # INPUT section
    st.markdown(
        '<p style="font-family:Inter,sans-serif;font-size:10px;font-weight:600;'
        'letter-spacing:0.15em;text-transform:uppercase;color:#64748b;'
        'padding:16px 4px 8px;margin:0;">INPUT</p>',
        unsafe_allow_html=True,
    )

    url_input = st.text_input(
        "YouTube URL",
        value=st.session_state.url,
        placeholder="youtube.com/watch?v=... or youtu.be/...",
        help="Supports standard, Shorts, and mobile URLs",
        key="url_field",
        label_visibility="collapsed",
    )

    url_valid = False
    video_id = None

    if url_input:
        st.session_state.url = url_input
        is_valid, result = validate_youtube_url(url_input)

        if is_valid:
            url_valid = True
            video_id = result
            st.session_state.video_id = video_id
            st.success(f"✓ Valid URL — Video ID: `{video_id}`")
        elif result:
            st.error(result)

    st.divider()

    # CUSTOMIZATION section
    st.markdown(
        '<p style="font-family:Inter,sans-serif;font-size:10px;font-weight:600;'
        'letter-spacing:0.15em;text-transform:uppercase;color:#64748b;'
        'padding:8px 4px;margin:0;">CUSTOMIZATION</p>',
        unsafe_allow_html=True,
    )

    tone = st.selectbox(
        "Writing Tone",
        ["Professional", "Casual", "Educational", "Storytelling", "Technical"],
        index=["Professional", "Casual", "Educational", "Storytelling", "Technical"].index(
            st.session_state.tone
        ),
        help="Sets the voice and style of the generated blog post",
    )
    st.session_state.tone = tone

    length_options = {
        "Short (~800 words)":   800,
        "Medium (~1500 words)": 1500,
        "Long (~2500 words)":   2500,
        "Epic (~4000 words)":   4000,
    }
    length_label = st.select_slider(
        "Content Length",
        options=list(length_options.keys()),
        value=st.session_state.length_label,
        help="Longer posts are more comprehensive but take more time",
    )
    st.session_state.length_label = length_label
    st.session_state.word_count_target = length_options[length_label]

    advanced_seo = st.checkbox(
        "Advanced SEO Mode",
        value=st.session_state.advanced_seo,
        help="Adds secondary keywords, heading suggestions, keyword density & link opportunities",
    )
    st.session_state.advanced_seo = advanced_seo
    st.session_state.seo_mode = "Advanced" if advanced_seo else "Basic"

    st.divider()

    # GENERATE BUTTON
    can_generate = url_valid and bool(GROQ_API_KEY) and st.session_state.stage != "processing"

    if st.button(
        "✨  Generate Blog Post",
        disabled=not can_generate,
        use_container_width=True,
        help=(
            "Start the 5-agent blog generation pipeline"
            if can_generate
            else ("Add GROQ_API_KEY to secrets.toml" if not GROQ_API_KEY
                  else "Enter a valid YouTube URL first")
        ),
    ):
        st.session_state.stage = "processing"
        st.session_state.error = None
        st.session_state.blog_content = ""
        for agent in st.session_state.agent_statuses:
            st.session_state.agent_statuses[agent] = {"status": "pending", "duration": 0}
        st.rerun()

    if not GROQ_API_KEY:
        st.caption("🔑 Add GROQ_API_KEY to secrets.toml")
    elif not url_valid:
        st.caption("Paste a YouTube URL above to get started")

    st.divider()

    # WORKFLOW PROGRESS section
    st.markdown(
        '<p style="font-family:Inter,sans-serif;font-size:10px;font-weight:600;'
        'letter-spacing:0.15em;text-transform:uppercase;color:#64748b;'
        'padding:8px 4px 4px;margin:0;">WORKFLOW PROGRESS</p>',
        unsafe_allow_html=True,
    )

    agent_info = [
        ("Research Analyst",   "🔬"),
        ("Content Strategist", "📐"),
        ("SEO Optimizer",      "🔍"),
        ("Blog Writer",        "✍️"),
        ("Quality Reviewer",   "✅"),
    ]

    # Build one single self-contained HTML block for all agent rows
    rows_html = ""
    for agent_name, icon in agent_info:
        ag = st.session_state.agent_statuses.get(agent_name, {"status": "pending", "duration": 0})
        status = ag["status"]
        duration = ag.get("duration", 0)

        if status == "active":
            dot_color = "#06b6d4"
            dot_anim = "animation:pulse-dot 1.5s ease infinite;"
            status_html = '<span style="color:#06b6d4;font-size:11px;">Working…</span>'
        elif status == "complete":
            dot_color = "#10b981"
            dot_anim = ""
            status_html = f'<span style="color:#10b981;font-size:11px;">✓ {duration}s</span>'
        else:
            dot_color = "#475569"
            dot_anim = ""
            status_html = '<span style="color:#475569;font-size:11px;">Pending</span>'

        rows_html += f"""
        <div style="display:flex;align-items:center;justify-content:space-between;
                    padding:7px 0;border-bottom:1px solid rgba(148,163,184,0.07);">
          <div style="display:flex;align-items:center;gap:8px;">
            <span style="width:9px;height:9px;border-radius:50%;background:{dot_color};
                         display:inline-block;flex-shrink:0;{dot_anim}"></span>
            <span style="font-family:Inter,sans-serif;font-size:13px;color:#f1f5f9;">
              {icon} {agent_name}
            </span>
          </div>
          {status_html}
        </div>
        """

    st.markdown(rows_html, unsafe_allow_html=True)

    # Overall progress bar
    completed = sum(1 for ag in st.session_state.agent_statuses.values() if ag["status"] == "complete")
    total = len(st.session_state.agent_statuses)
    if completed > 0:
        pct = int((completed / total) * 100)
        st.markdown(f"""
<div style="margin-top:12px;">
  <div style="display:flex;justify-content:space-between;font-size:11px;color:#64748b;margin-bottom:4px;">
    <span>Overall Progress</span><span>{pct}%</span>
  </div>
  <div style="background:#2d4158;border-radius:4px;height:4px;overflow:hidden;">
    <div style="width:{pct}%;height:100%;background:linear-gradient(90deg,#ec4899,#a855f7,#06b6d4);
                border-radius:4px;"></div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown(
        '<p style="font-size:11px;color:#475569;text-align:center;margin-top:20px;">'
        'DocMind Studio v2.0 · 5-Agent CrewAI</p>',
        unsafe_allow_html=True,
    )


# ── MAIN CONTENT ─────────────────────────────────────────────────────────────

# ════════════════════════════════════════
# STAGE: INPUT
# ════════════════════════════════════════
if st.session_state.stage == "input":

    if st.session_state.error:
        st.markdown(f"""
<div style="background:rgba(26,35,50,1);border:1px solid rgba(148,163,184,0.12);
     border-left:3px solid #f43f5e;border-radius:12px;padding:20px;margin-bottom:24px;">
  <div style="font-size:22px;margin-bottom:6px;">⚠️</div>
  <div style="font-family:Inter,sans-serif;font-size:15px;font-weight:600;
              color:#f1f5f9;margin-bottom:6px;">Something went wrong</div>
  <div style="font-family:Inter,sans-serif;font-size:13px;color:#cbd5e1;line-height:1.6;">
    {st.session_state.error}
  </div>
</div>
""", unsafe_allow_html=True)

    # Hero area
    st.markdown("""
<div style="background:linear-gradient(135deg,rgba(236,72,153,0.12) 0%,rgba(168,85,247,0.07) 50%,transparent 100%);
     border-radius:24px;padding:64px 40px;text-align:center;margin-bottom:20px;">

  <div style="font-size:60px;animation:float 4s ease-in-out infinite;display:block;margin-bottom:20px;">✨</div>

  <div style="font-family:'Bricolage Grotesque',sans-serif;font-size:38px;font-weight:600;
              color:#f1f5f9;margin-bottom:16px;line-height:1.2;">
    Transform Videos into Blog Posts
  </div>

  <div style="font-family:Inter,sans-serif;font-size:16px;color:#cbd5e1;
              max-width:500px;margin:0 auto 36px;line-height:1.7;">
    Paste a YouTube URL in the sidebar to automatically convert video content
    into SEO-optimized, publication-ready blog posts using 5 specialized AI agents.
  </div>

  <div style="display:flex;gap:14px;justify-content:center;flex-wrap:wrap;">
    <div style="background:rgba(236,72,153,0.1);border:1px solid rgba(236,72,153,0.25);
         border-radius:12px;padding:16px 18px;text-align:center;min-width:120px;">
      <div style="font-size:26px;margin-bottom:6px;">🔬</div>
      <div style="font-size:13px;color:#cbd5e1;font-weight:500;">Research Agent</div>
      <div style="font-size:11px;color:#64748b;margin-top:3px;">Analyzes depth</div>
    </div>
    <div style="background:rgba(168,85,247,0.1);border:1px solid rgba(168,85,247,0.25);
         border-radius:12px;padding:16px 18px;text-align:center;min-width:120px;">
      <div style="font-size:26px;margin-bottom:6px;">📐</div>
      <div style="font-size:13px;color:#cbd5e1;font-weight:500;">Strategy Agent</div>
      <div style="font-size:11px;color:#64748b;margin-top:3px;">Structures outline</div>
    </div>
    <div style="background:rgba(6,182,212,0.1);border:1px solid rgba(6,182,212,0.25);
         border-radius:12px;padding:16px 18px;text-align:center;min-width:120px;">
      <div style="font-size:26px;margin-bottom:6px;">🔍</div>
      <div style="font-size:13px;color:#cbd5e1;font-weight:500;">SEO Agent</div>
      <div style="font-size:11px;color:#64748b;margin-top:3px;">Optimizes search</div>
    </div>
    <div style="background:rgba(236,72,153,0.08);border:1px solid rgba(236,72,153,0.18);
         border-radius:12px;padding:16px 18px;text-align:center;min-width:120px;">
      <div style="font-size:26px;margin-bottom:6px;">✍️</div>
      <div style="font-size:13px;color:#cbd5e1;font-weight:500;">Writer Agent</div>
      <div style="font-size:11px;color:#64748b;margin-top:3px;">Writes content</div>
    </div>
    <div style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.22);
         border-radius:12px;padding:16px 18px;text-align:center;min-width:120px;">
      <div style="font-size:26px;margin-bottom:6px;">✅</div>
      <div style="font-size:13px;color:#cbd5e1;font-weight:500;">Review Agent</div>
      <div style="font-size:11px;color:#64748b;margin-top:3px;">Polishes output</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown(get_stage_bar_html(0), unsafe_allow_html=True)


# ════════════════════════════════════════
# STAGE: PROCESSING
# ════════════════════════════════════════
elif st.session_state.stage == "processing":

    agent_defs = [
        ("Research Analyst",   "🔬", ["Analyzing video structure…", "Extracting key concepts…", "Identifying main arguments…", "Detecting important topics…"]),
        ("Content Strategist", "📐", ["Organizing research findings…", "Creating blog outline…", "Designing section hierarchy…", "Planning content flow…"]),
        ("SEO Optimizer",      "🔍", ["Generating SEO title…", "Writing meta description…", "Finding primary keyword…", "Building keyword strategy…"]),
        ("Blog Writer",        "✍️", ["Writing introduction…", "Developing main sections…", "Adding examples…", "Crafting conclusion and CTA…"]),
        ("Quality Reviewer",   "✅", ["Checking grammar and style…", "Eliminating redundancy…", "Verifying tone consistency…", "Final polish…"]),
    ]

    st.markdown("""
<div style="margin-bottom:24px;">
  <div style="font-family:'Bricolage Grotesque',sans-serif;font-size:26px;font-weight:600;
              color:#f1f5f9;margin-bottom:8px;">🤖 Multi-Agent Pipeline Running</div>
  <div style="font-family:Inter,sans-serif;font-size:14px;color:#cbd5e1;">
    5 specialized AI agents are collaborating to transform your video into a blog post
  </div>
</div>
""", unsafe_allow_html=True)

    # Transcript fetch indicator
    transcript_ph = st.empty()
    transcript_ph.markdown("""
<div style="background:#1a2332;border:1px solid rgba(6,182,212,0.3);
     border-radius:12px;padding:16px 20px;margin-bottom:16px;
     display:flex;align-items:center;gap:12px;">
  <span style="font-size:22px;">📥</span>
  <div>
    <div style="font-size:14px;font-weight:600;color:#f1f5f9;">Extracting transcript from YouTube…</div>
    <div style="font-size:12px;color:#64748b;margin-top:2px;">Fetching captions and timestamps</div>
  </div>
</div>
""", unsafe_allow_html=True)

    success, formatted, raw, err_msg = fetch_transcript(st.session_state.video_id)
    transcript_ph.empty()

    if not success:
        st.session_state.stage = "input"
        st.session_state.error = err_msg
        st.rerun()

    st.session_state.transcript_formatted = formatted
    st.session_state.transcript_raw = raw

    # Agent card placeholders
    placeholders = {name: st.empty() for name, _, _ in agent_defs}
    for name, icon, _ in agent_defs:
        placeholders[name].markdown(
            get_agent_card_html(name, icon, "pending", [], 0),
            unsafe_allow_html=True,
        )

    stage_ph = st.empty()
    stage_ph.markdown(get_stage_bar_html(1), unsafe_allow_html=True)

    # Run pipeline
    try:
        from agents import run_agent_pipeline

        raw_to_process = chunk_transcript(st.session_state.transcript_raw, max_words=7000)
        gen_start = time.time()

        def on_agent_start(idx, name):
            ag_key = list(st.session_state.agent_statuses.keys())[idx]
            st.session_state.agent_statuses[ag_key]["status"] = "active"
            _, icon, tasks = agent_defs[idx]
            placeholders[name].markdown(
                get_agent_card_html(name, icon, "active", tasks[:2], 35),
                unsafe_allow_html=True,
            )
            stage_ph.markdown(get_stage_bar_html(idx + 1), unsafe_allow_html=True)

        def on_agent_complete(idx, name, duration):
            ag_key = list(st.session_state.agent_statuses.keys())[idx]
            st.session_state.agent_statuses[ag_key]["status"] = "complete"
            st.session_state.agent_statuses[ag_key]["duration"] = duration
            _, icon, tasks = agent_defs[idx]
            placeholders[name].markdown(
                get_agent_card_html(name, icon, "complete", tasks, 100, duration),
                unsafe_allow_html=True,
            )

        result = run_agent_pipeline(
            api_key=GROQ_API_KEY,
            transcript=raw_to_process,
            tone=st.session_state.tone,
            word_count=st.session_state.word_count_target,
            seo_mode=st.session_state.seo_mode,
            progress_callbacks={
                "on_agent_start": on_agent_start,
                "on_agent_complete": on_agent_complete,
            },
        )

        st.session_state.blog_content = result["blog_content"]
        st.session_state.seo_metadata = parse_blog_metadata(result["blog_content"])
        st.session_state.generation_time = round(time.time() - gen_start, 1)
        st.session_state.stage = "output"
        st.rerun()

    except Exception as e:
        err_str = str(e)
        if "rate" in err_str.lower() or "429" in err_str:
            msg = "⏱ Rate limit reached. Please wait 60 seconds and try again."
        elif "invalid" in err_str.lower() and "api" in err_str.lower():
            msg = "🔑 Invalid API key. Please check your GROQ_API_KEY in secrets.toml."
        elif "token" in err_str.lower() and "limit" in err_str.lower():
            msg = "📄 Video is too long for the free tier. Try a shorter video (under 30 min)."
        else:
            msg = f"Generation failed: {err_str[:200]}. Please try again."
        st.session_state.error = msg
        st.session_state.stage = "input"
        st.rerun()


# ════════════════════════════════════════
# STAGE: OUTPUT
# ════════════════════════════════════════
elif st.session_state.stage == "output":

    blog = st.session_state.blog_content
    meta = st.session_state.seo_metadata
    wc = count_words(blog)
    tone_label = st.session_state.tone
    seo_mode = st.session_state.seo_mode
    gen_time = st.session_state.generation_time

    st.markdown(f"""
<div style="margin-bottom:24px;">
  <div style="font-family:'Bricolage Grotesque',sans-serif;font-size:26px;
              font-weight:600;color:#f1f5f9;margin-bottom:4px;">📝 Blog Post Generated</div>
  <div style="font-family:Inter,sans-serif;font-size:13px;color:#64748b;">
    {format_word_count(wc)} · {tone_label} Tone · {seo_mode} SEO · Generated in {gen_time}s
  </div>
</div>
""", unsafe_allow_html=True)

    # SEO section
    st.markdown(get_seo_section_html(
        meta.get("seo_title", ""),
        meta.get("meta_description", ""),
        meta.get("primary_keyword", ""),
        meta.get("secondary_keywords", []),
    ), unsafe_allow_html=True)

    # Gradient divider
    st.markdown("""
<hr style="border:none;height:1px;
    background:linear-gradient(90deg,#ec4899,#a855f7,transparent);margin:28px 0;">
""", unsafe_allow_html=True)

    # Blog body with Newsreader typography
    clean_blog = clean_blog_for_display(blog)
    blog_html = md.markdown(clean_blog, extensions=['fenced_code', 'tables'])

    st.markdown(f"""
<div style="background:#1a2332;border:1px solid rgba(148,163,184,0.12);
     border-radius:16px;padding:40px;">
  <div style="font-family:'Newsreader',Georgia,serif;font-size:17px;
              line-height:1.8;color:#f1f5f9;">
    {blog_html}
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown(get_stage_bar_html(5), unsafe_allow_html=True)

    # Export buttons
    st.markdown("""
<div style="margin-top:28px;margin-bottom:12px;font-family:Inter,sans-serif;
     font-size:10px;font-weight:600;letter-spacing:0.15em;
     text-transform:uppercase;color:#64748b;">EXPORT YOUR BLOG POST</div>
""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            label="⬇ Download Markdown (.md)",
            data=blog,
            file_name=f"docmind-{st.session_state.video_id}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            label="⬇ Download Text (.txt)",
            data=clean_blog,
            file_name=f"docmind-{st.session_state.video_id}.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with col3:
        seo_title_safe = meta.get("seo_title", "Blog Post").replace('"', '&quot;')
        meta_desc_safe = meta.get("meta_description", "").replace('"', '&quot;')
        st.download_button(
            label="⬇ Download HTML (.html)",
            data=f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>{seo_title_safe}</title>
<meta name="description" content="{meta_desc_safe}">
<style>
body{{max-width:800px;margin:60px auto;font-family:Georgia,serif;
     font-size:18px;line-height:1.8;color:#1a1a1a;padding:0 20px}}
h1{{font-size:36px}}h2{{font-size:28px}}h3{{font-size:22px}}
pre{{background:#f4f4f4;padding:16px;border-radius:8px;overflow-x:auto}}
code{{background:#f0f0f0;padding:2px 6px;border-radius:4px}}
blockquote{{border-left:3px solid #ec4899;padding:12px 20px;background:#fafafa}}
</style></head>
<body>{blog_html}</body></html>""",
            file_name=f"docmind-{st.session_state.video_id}.html",
            mime="text/html",
            use_container_width=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📋 View & Copy Raw Markdown"):
        st.code(blog, language="markdown")

    st.markdown("<br>", unsafe_allow_html=True)
    _, btn_col = st.columns([4, 1])
    with btn_col:
        if st.button("🔄 Generate Another", use_container_width=True):
            st.session_state.update({
                "stage": "input",
                "url": "",
                "video_id": None,
                "blog_content": "",
                "transcript_formatted": "",
                "transcript_raw": "",
                "seo_metadata": {},
                "error": None,
            })
            for agent in st.session_state.agent_statuses:
                st.session_state.agent_statuses[agent] = {"status": "pending", "duration": 0}
            st.rerun()
