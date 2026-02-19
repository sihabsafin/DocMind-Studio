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

# Page config — MUST be first
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

# Inject styles
st.markdown(FONTS_AND_STYLES, unsafe_allow_html=True)

# ── Resolve API key (secrets → env var, never from UI) ──────────────────────
def get_groq_api_key() -> str:
    try:
        key = st.secrets.get("GROQ_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("GROQ_API_KEY", "")

GROQ_API_KEY = get_groq_api_key()

# ============================
# SESSION STATE
# ============================
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
            "Research Analyst":    {"status": "pending", "duration": 0, "progress": 0},
            "Content Strategist":  {"status": "pending", "duration": 0, "progress": 0},
            "SEO Optimizer":       {"status": "pending", "duration": 0, "progress": 0},
            "Blog Writer":         {"status": "pending", "duration": 0, "progress": 0},
            "Quality Reviewer":    {"status": "pending", "duration": 0, "progress": 0},
        },
        "error": None,
        "generation_time": 0,
        "tone": "Professional",
        "length_label": "Medium (~1500 words)",
        "advanced_seo": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_state()

# ============================
# TOP BAR
# ============================
api_badge = (
    '<span style="color:#10b981;font-size:8px;">●</span> API Ready'
    if GROQ_API_KEY else
    '<span style="color:#f43f5e;font-size:8px;">●</span> No API Key'
)

st.markdown(f"""
<div class="docmind-topbar">
  <div class="docmind-logo">
    <div class="docmind-logo-icon">◈</div>
    <span class="docmind-logo-text">DocMind Studio</span>
  </div>
  <div style="display:flex;align-items:center;gap:10px;">
    <div class="docmind-status-pill">{api_badge}</div>
    <div class="docmind-status-pill">⚡ Groq · Llama 3.3 70B</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── API key warning banner (only if missing) ────────────────────────────────
if not GROQ_API_KEY:
    st.markdown("""
    <div style="background:rgba(244,63,94,0.1);border:1px solid rgba(244,63,94,0.4);
         border-radius:10px;padding:14px 20px;margin-bottom:16px;display:flex;align-items:center;gap:10px;">
      <span style="font-size:20px;">🔑</span>
      <div>
        <div style="font-family:var(--font-ui);font-size:14px;font-weight:600;color:var(--text-primary);">
          Groq API Key Required
        </div>
        <div style="font-size:12px;color:var(--text-secondary);">
          Add <code>GROQ_API_KEY = "gsk_..."</code> to your 
          <strong>.streamlit/secrets.toml</strong> file or set it as an environment variable.
          Get a free key at <strong>console.groq.com</strong>.
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ============================
# SIDEBAR
# ============================
with st.sidebar:

    # ─── INPUT ───
    st.markdown('<div class="section-header">Input</div>', unsafe_allow_html=True)
    st.markdown('<div style="padding:0 20px 16px;">', unsafe_allow_html=True)

    url_input = st.text_input(
        "YouTube URL",
        value=st.session_state.url,
        placeholder="youtube.com/watch?v=... or youtu.be/...",
        help="Paste any YouTube video URL — standard, shorts, or mobile format",
        key="url_input_field",
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
            st.markdown(
                f'<div class="url-valid">✓ Valid YouTube URL detected</div>',
                unsafe_allow_html=True,
            )
            st.markdown(f"""
            <div class="video-preview-card">
              <div class="video-preview-title">🎬 Video ID: {video_id}</div>
              <div class="video-preview-meta">Ready to extract transcript</div>
            </div>
            """, unsafe_allow_html=True)
        elif result:
            st.markdown(f'<div class="url-error">⚠ {result}</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<hr style="border:none;border-top:1px solid rgba(148,163,184,0.12);margin:0;">', unsafe_allow_html=True)

    # ─── CUSTOMIZATION ───
    st.markdown('<div class="section-header">Customization</div>', unsafe_allow_html=True)
    st.markdown('<div style="padding:0 20px 16px;">', unsafe_allow_html=True)

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
    word_count_target = length_options[length_label]

    advanced_seo = st.checkbox(
        "Advanced SEO Mode",
        value=st.session_state.advanced_seo,
        help="Includes secondary keywords, heading optimization, keyword density & link opportunities",
    )
    st.session_state.advanced_seo = advanced_seo
    seo_mode = "Advanced" if advanced_seo else "Basic"

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<hr style="border:none;border-top:1px solid rgba(148,163,184,0.12);margin:0;">', unsafe_allow_html=True)

    # ─── GENERATE BUTTON ───
    st.markdown('<div style="padding:16px 20px;">', unsafe_allow_html=True)

    can_generate = url_valid and GROQ_API_KEY and st.session_state.stage not in ["processing"]

    if st.button(
        "✨  Generate Blog Post",
        disabled=not can_generate,
        help=(
            "Start the multi-agent blog generation pipeline"
            if can_generate
            else (
                "Set GROQ_API_KEY in secrets.toml"
                if not GROQ_API_KEY
                else "Enter a valid YouTube URL first"
            )
        ),
    ):
        st.session_state.stage = "processing"
        st.session_state.error = None
        st.session_state.blog_content = ""
        for agent in st.session_state.agent_statuses:
            st.session_state.agent_statuses[agent] = {"status": "pending", "duration": 0, "progress": 0}
        st.rerun()

    if not GROQ_API_KEY:
        st.markdown(
            '<div style="font-size:11px;color:var(--accent-rose);text-align:center;margin-top:8px;">'
            '🔑 Add GROQ_API_KEY to secrets.toml</div>',
            unsafe_allow_html=True,
        )
    elif not url_valid:
        st.markdown(
            '<div style="font-size:12px;color:var(--text-muted);text-align:center;margin-top:8px;">'
            'Enter a valid YouTube URL above</div>',
            unsafe_allow_html=True,
        )

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<hr style="border:none;border-top:1px solid rgba(148,163,184,0.12);margin:0;">', unsafe_allow_html=True)

    # ─── WORKFLOW PROGRESS ───
    st.markdown('<div class="section-header">Workflow Progress</div>', unsafe_allow_html=True)
    st.markdown('<div style="padding:0 20px 20px;">', unsafe_allow_html=True)

    agent_info = [
        ("Research Analyst",   "🔬"),
        ("Content Strategist", "📐"),
        ("SEO Optimizer",      "🔍"),
        ("Blog Writer",        "✍️"),
        ("Quality Reviewer",   "✅"),
    ]

    progress_html = '<div class="agent-progress-container">'
    for agent_name, icon in agent_info:
        ag = st.session_state.agent_statuses.get(agent_name, {"status": "pending", "duration": 0})
        status = ag["status"]
        duration = ag.get("duration", 0)

        if status == "pending":
            dot = '<span class="agent-dot agent-dot-pending"></span>'
            st_text = '<span style="color:var(--text-dim);font-size:11px;">Pending</span>'
        elif status == "active":
            dot = '<span class="agent-dot agent-dot-active"></span>'
            st_text = '<span style="color:var(--accent-cyan);font-size:11px;">Working…</span>'
        else:
            dot = '<span class="agent-dot agent-dot-complete"></span>'
            st_text = f'<span style="color:var(--accent-emerald);font-size:11px;">✓ {duration}s</span>'

        progress_html += f"""
        <div class="agent-progress-item">
          <div style="display:flex;align-items:center;">{dot}
            <span class="agent-name">{icon} {agent_name}</span>
          </div>
          {st_text}
        </div>
        """
    progress_html += '</div>'
    st.markdown(progress_html, unsafe_allow_html=True)

    completed = sum(1 for ag in st.session_state.agent_statuses.values() if ag["status"] == "complete")
    total = len(st.session_state.agent_statuses)
    if completed > 0:
        pct = int((completed / total) * 100)
        st.markdown(f"""
        <div style="margin-top:12px;">
          <div style="display:flex;justify-content:space-between;font-size:11px;color:var(--text-muted);margin-bottom:4px;">
            <span>Overall Progress</span><span>{pct}%</span>
          </div>
          <div class="progress-bar-container">
            <div class="progress-bar-fill" style="width:{pct}%;"></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div style="padding:14px 20px;border-top:1px solid rgba(148,163,184,0.12);">
      <div style="font-size:11px;color:var(--text-dim);text-align:center;line-height:1.6;">
        DocMind Studio v2.0 · 5-Agent CrewAI Pipeline
      </div>
    </div>
    """, unsafe_allow_html=True)


# ============================
# MAIN CONTENT AREA
# ============================

# ── STAGE: INPUT ──────────────────────────────────────────────────────────────
if st.session_state.stage == "input":

    if st.session_state.error:
        st.markdown(f"""
        <div class="error-card" style="margin-bottom:20px;">
          <div class="error-icon">⚠️</div>
          <div class="error-title">Something went wrong</div>
          <div class="error-message">{st.session_state.error}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="hero-state">
      <span class="hero-icon">✨</span>
      <div class="hero-title">Transform Videos into Blog Posts</div>
      <div class="hero-subtitle">
        Paste a YouTube URL in the sidebar to automatically convert video content
        into SEO-optimized, publication-ready blog posts using 5 specialized AI agents.
      </div>
      <div style="display:flex;gap:16px;justify-content:center;flex-wrap:wrap;margin-top:32px;">
        <div style="background:rgba(236,72,153,0.1);border:1px solid rgba(236,72,153,0.2);border-radius:12px;padding:16px 20px;text-align:center;min-width:130px;">
          <div style="font-size:28px;margin-bottom:6px;">🔬</div>
          <div style="font-family:var(--font-ui);font-size:13px;color:var(--text-secondary);font-weight:500;">Research Agent</div>
          <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">Analyzes content depth</div>
        </div>
        <div style="background:rgba(168,85,247,0.1);border:1px solid rgba(168,85,247,0.2);border-radius:12px;padding:16px 20px;text-align:center;min-width:130px;">
          <div style="font-size:28px;margin-bottom:6px;">📐</div>
          <div style="font-family:var(--font-ui);font-size:13px;color:var(--text-secondary);font-weight:500;">Strategy Agent</div>
          <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">Structures the outline</div>
        </div>
        <div style="background:rgba(6,182,212,0.1);border:1px solid rgba(6,182,212,0.2);border-radius:12px;padding:16px 20px;text-align:center;min-width:130px;">
          <div style="font-size:28px;margin-bottom:6px;">🔍</div>
          <div style="font-family:var(--font-ui);font-size:13px;color:var(--text-secondary);font-weight:500;">SEO Agent</div>
          <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">Optimizes for search</div>
        </div>
        <div style="background:rgba(236,72,153,0.08);border:1px solid rgba(236,72,153,0.15);border-radius:12px;padding:16px 20px;text-align:center;min-width:130px;">
          <div style="font-size:28px;margin-bottom:6px;">✍️</div>
          <div style="font-family:var(--font-ui);font-size:13px;color:var(--text-secondary);font-weight:500;">Writer Agent</div>
          <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">Writes full content</div>
        </div>
        <div style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.2);border-radius:12px;padding:16px 20px;text-align:center;min-width:130px;">
          <div style="font-size:28px;margin-bottom:6px;">✅</div>
          <div style="font-family:var(--font-ui);font-size:13px;color:var(--text-secondary);font-weight:500;">Review Agent</div>
          <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">Polishes to publish</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(get_stage_bar_html(0), unsafe_allow_html=True)


# ── STAGE: PROCESSING ─────────────────────────────────────────────────────────
elif st.session_state.stage == "processing":

    agent_names = [
        ("Research Analyst",   "🔬", ["Analyzing video structure…", "Extracting key concepts…", "Identifying main arguments…", "Detecting important topics…"]),
        ("Content Strategist", "📐", ["Organizing research findings…", "Creating blog outline…", "Designing section hierarchy…", "Planning content flow…"]),
        ("SEO Optimizer",      "🔍", ["Generating SEO title…", "Writing meta description…", "Finding primary keyword…", "Building keyword strategy…"]),
        ("Blog Writer",        "✍️", ["Writing introduction…", "Developing main sections…", "Adding examples and detail…", "Crafting conclusion and CTA…"]),
        ("Quality Reviewer",   "✅", ["Checking grammar and style…", "Eliminating redundancy…", "Verifying tone consistency…", "Final polish and review…"]),
    ]

    st.markdown("""
    <div style="margin-bottom:24px;">
      <div style="font-family:var(--font-display);font-size:28px;font-weight:600;color:var(--text-primary);margin-bottom:8px;">
        🤖 Multi-Agent Pipeline Running
      </div>
      <div style="font-family:var(--font-ui);font-size:15px;color:var(--text-secondary);">
        5 specialized AI agents are collaborating to transform your video into a blog post
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Transcript extraction ──
    transcript_placeholder = st.empty()
    transcript_placeholder.markdown("""
    <div style="background:var(--color-surface-1);border:1px solid rgba(6,182,212,0.3);
         border-radius:12px;padding:16px 20px;margin-bottom:16px;display:flex;align-items:center;gap:12px;">
      <span style="font-size:20px;">📥</span>
      <div>
        <div style="font-family:var(--font-ui);font-size:14px;font-weight:600;color:var(--text-primary);">
          Extracting transcript from YouTube…
        </div>
        <div style="font-size:12px;color:var(--text-muted);">Fetching captions and timestamps</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    success, formatted, raw, err_msg = fetch_transcript(st.session_state.video_id)
    transcript_placeholder.empty()

    if not success:
        st.session_state.stage = "input"
        st.session_state.error = err_msg
        st.rerun()

    st.session_state.transcript_formatted = formatted
    st.session_state.transcript_raw = raw

    # ── Agent cards ──
    placeholders = {}
    for name, icon, tasks in agent_names:
        placeholders[name] = st.empty()
        placeholders[name].markdown(
            get_agent_card_html(name, icon, "pending", [], 0),
            unsafe_allow_html=True,
        )

    stage_placeholder = st.empty()
    stage_placeholder.markdown(get_stage_bar_html(1), unsafe_allow_html=True)

    # ── Run pipeline ──
    try:
        from agents import run_agent_pipeline

        raw_to_process = chunk_transcript(st.session_state.transcript_raw, max_words=7000)
        gen_start = time.time()

        def on_agent_start(idx, name):
            agent_key = list(st.session_state.agent_statuses.keys())[idx]
            st.session_state.agent_statuses[agent_key]["status"] = "active"
            _, icon, tasks = agent_names[idx]
            placeholders[name].markdown(
                get_agent_card_html(name, icon, "active", tasks[:2], 35),
                unsafe_allow_html=True,
            )
            stage_placeholder.markdown(get_stage_bar_html(idx + 1), unsafe_allow_html=True)

        def on_agent_complete(idx, name, duration):
            agent_key = list(st.session_state.agent_statuses.keys())[idx]
            st.session_state.agent_statuses[agent_key]["status"] = "complete"
            st.session_state.agent_statuses[agent_key]["duration"] = duration
            _, icon, tasks = agent_names[idx]
            placeholders[name].markdown(
                get_agent_card_html(name, icon, "complete", tasks, 100, duration),
                unsafe_allow_html=True,
            )

        result = run_agent_pipeline(
            api_key=GROQ_API_KEY,
            transcript=raw_to_process,
            tone=st.session_state.tone,
            word_count=word_count_target,
            seo_mode=seo_mode,
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
            st.session_state.error = "⏱ Rate limit reached. Please wait 60 seconds and try again."
        elif "invalid" in err_str.lower() and "api" in err_str.lower():
            st.session_state.error = "🔑 Invalid API key. Please check your GROQ_API_KEY in secrets.toml."
        elif "token" in err_str.lower() and "limit" in err_str.lower():
            st.session_state.error = "📄 Video is too long for the free tier. Try a shorter video (under 30 minutes)."
        else:
            st.session_state.error = f"Generation failed: {err_str[:200]}. Please try again."
        st.session_state.stage = "input"
        st.rerun()


# ── STAGE: OUTPUT ─────────────────────────────────────────────────────────────
elif st.session_state.stage == "output":

    blog = st.session_state.blog_content
    meta = st.session_state.seo_metadata
    wc = count_words(blog)
    tone_label = st.session_state.tone
    gen_time = st.session_state.generation_time

    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:24px;">
      <div>
        <div style="font-family:var(--font-display);font-size:28px;font-weight:600;color:var(--text-primary);margin-bottom:4px;">
          📝 Blog Post Generated
        </div>
        <div style="font-family:var(--font-ui);font-size:14px;color:var(--text-muted);">
          {format_word_count(wc)} · {tone_label} Tone · {seo_mode} SEO · Generated in {gen_time}s
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(get_seo_section_html(
        meta.get("seo_title", ""),
        meta.get("meta_description", ""),
        meta.get("primary_keyword", ""),
        meta.get("secondary_keywords", []),
    ), unsafe_allow_html=True)

    st.markdown('<hr class="blog-divider">', unsafe_allow_html=True)

    clean_blog = clean_blog_for_display(blog)
    blog_html = md.markdown(clean_blog, extensions=['fenced_code', 'tables'])

    st.markdown(f"""
    <div class="blog-output-card">
      <div class="blog-content">
        {blog_html}
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(get_stage_bar_html(5), unsafe_allow_html=True)

    # ── Exports ──
    st.markdown("""
    <div style="margin-top:32px;">
      <div class="sidebar-label" style="padding:0;margin-bottom:12px;">Export Your Blog Post</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            label="⬇ Download Markdown (.md)",
            data=blog,
            file_name=f"docmind-{st.session_state.video_id}.md",
            mime="text/markdown",
        )

    with col2:
        st.download_button(
            label="⬇ Download Text (.txt)",
            data=clean_blog,
            file_name=f"docmind-{st.session_state.video_id}.txt",
            mime="text/plain",
        )

    seo_title_safe = meta.get('seo_title', 'Blog Post').replace('"', '&quot;')
    meta_desc_safe = meta.get('meta_description', '').replace('"', '&quot;')

    with col3:
        st.download_button(
            label="⬇ Download HTML (.html)",
            data=f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>{seo_title_safe}</title>
  <meta name="description" content="{meta_desc_safe}">
  <style>
    body{{max-width:800px;margin:60px auto;font-family:Georgia,serif;font-size:18px;line-height:1.8;color:#1a1a1a;padding:0 20px}}
    h1{{font-size:36px}}h2{{font-size:28px}}h3{{font-size:22px}}
    pre{{background:#f4f4f4;padding:16px;border-radius:8px;overflow-x:auto}}
    code{{background:#f0f0f0;padding:2px 6px;border-radius:4px;font-size:14px}}
    blockquote{{border-left:3px solid #ec4899;padding:12px 20px;background:#fafafa}}
  </style>
</head>
<body>{blog_html}</body>
</html>""",
            file_name=f"docmind-{st.session_state.video_id}.html",
            mime="text/html",
        )

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📋 View & Copy Raw Markdown"):
        st.code(blog, language="markdown")

    st.markdown("<br>", unsafe_allow_html=True)
    _, col_btn = st.columns([4, 1])
    with col_btn:
        if st.button("🔄 Generate Another"):
            for k in ["stage", "url", "video_id", "blog_content",
                      "transcript_formatted", "transcript_raw", "seo_metadata", "error"]:
                st.session_state[k] = (
                    "input" if k == "stage" else
                    None if k in ["video_id"] else
                    {} if k == "seo_metadata" else
                    None if k == "error" else ""
                )
            for agent in st.session_state.agent_statuses:
                st.session_state.agent_statuses[agent] = {"status": "pending", "duration": 0, "progress": 0}
            st.rerun()
