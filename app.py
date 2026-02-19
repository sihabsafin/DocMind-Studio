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
from io import StringIO

# Page config — MUST be first
st.set_page_config(
    page_title="DocMind Studio",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Import local modules
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

# ============================
# SESSION STATE INITIALIZATION
# ============================
def init_session_state():
    defaults = {
        "stage": "input",  # input, transcript, processing, output, success
        "url": "",
        "video_id": None,
        "transcript_formatted": "",
        "transcript_raw": "",
        "blog_content": "",
        "seo_metadata": {},
        "agent_statuses": {
            "Research Analyst": {"status": "pending", "duration": 0, "progress": 0},
            "Content Strategist": {"status": "pending", "duration": 0, "progress": 0},
            "SEO Optimizer": {"status": "pending", "duration": 0, "progress": 0},
            "Blog Writer": {"status": "pending", "duration": 0, "progress": 0},
            "Quality Reviewer": {"status": "pending", "duration": 0, "progress": 0},
        },
        "error": None,
        "generation_time": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_state()

# ============================
# TOP BAR
# ============================
st.markdown("""
<div class="docmind-topbar">
  <div class="docmind-logo">
    <div class="docmind-logo-icon">◈</div>
    <span class="docmind-logo-text">DocMind Studio</span>
  </div>
  <div style="display: flex; align-items: center; gap: 12px;">
    <div class="docmind-status-pill">
      <span style="color: #10b981; font-size: 8px;">●</span>
      Multi-Agent AI Ready
    </div>
    <div class="docmind-status-pill">⚡ Groq · Llama 3.3 70B</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ============================
# SIDEBAR
# ============================
with st.sidebar:
    
    # ─── API KEY ───
    st.markdown('<div class="section-header">API Configuration</div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div style="padding: 0 20px 16px;">', unsafe_allow_html=True)
        
        # Try to get from secrets first
        default_key = ""
        try:
            default_key = st.secrets.get("GROQ_API_KEY", "")
        except:
            pass
        
        groq_api_key = st.text_input(
            "Groq API Key",
            value=default_key,
            type="password",
            placeholder="gsk_...",
            help="Get your free API key from console.groq.com",
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<hr style="border: none; border-top: 1px solid rgba(148,163,184,0.12); margin: 0;">', unsafe_allow_html=True)
    
    # ─── URL INPUT ───
    st.markdown('<div class="section-header">Input</div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div style="padding: 0 20px 16px;">', unsafe_allow_html=True)
        
        url_input = st.text_input(
            "YouTube URL",
            value=st.session_state.url,
            placeholder="youtube.com/watch?v=...",
            help="Paste any YouTube video URL — standard, shorts, or mobile format",
            key="url_input_field",
        )
        
        # URL Validation
        url_valid = False
        video_id = None
        
        if url_input:
            st.session_state.url = url_input
            is_valid, result = validate_youtube_url(url_input)
            
            if is_valid:
                url_valid = True
                video_id = result
                st.session_state.video_id = video_id
                st.markdown(f'<div class="url-valid">✓ Valid YouTube URL detected</div>', unsafe_allow_html=True)
                st.markdown(f"""
                <div class="video-preview-card">
                  <div class="video-preview-title">🎬 Video ID: {video_id}</div>
                  <div class="video-preview-meta">Ready to extract transcript</div>
                </div>
                """, unsafe_allow_html=True)
            elif result:  # has error message
                st.markdown(f'<div class="url-error">⚠ {result}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<hr style="border: none; border-top: 1px solid rgba(148,163,184,0.12); margin: 0;">', unsafe_allow_html=True)
    
    # ─── CUSTOMIZATION ───
    st.markdown('<div class="section-header">Customization</div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div style="padding: 0 20px 16px;">', unsafe_allow_html=True)
        
        tone = st.selectbox(
            "Writing Tone",
            ["Professional", "Casual", "Educational", "Storytelling", "Technical"],
            index=0,
            help="Sets the voice and style of the generated blog post",
        )
        
        tone_icons = {
            "Professional": "✍️",
            "Casual": "💼",
            "Educational": "🎓",
            "Storytelling": "📖",
            "Technical": "🔬",
        }
        
        length_options = {
            "Short (~800 words)": 800,
            "Medium (~1500 words)": 1500,
            "Long (~2500 words)": 2500,
            "Epic (~4000 words)": 4000,
        }
        
        length_label = st.select_slider(
            "Content Length",
            options=list(length_options.keys()),
            value="Medium (~1500 words)",
            help="Longer posts are more comprehensive but take more time to generate",
        )
        word_count_target = length_options[length_label]
        
        advanced_seo = st.checkbox(
            "Advanced SEO Mode",
            value=False,
            help="Includes secondary keywords, heading optimization, keyword density analysis, and link opportunities",
        )
        seo_mode = "Advanced" if advanced_seo else "Basic"
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<hr style="border: none; border-top: 1px solid rgba(148,163,184,0.12); margin: 0;">', unsafe_allow_html=True)
    
    # ─── GENERATE BUTTON ───
    with st.container():
        st.markdown('<div style="padding: 16px 20px;">', unsafe_allow_html=True)
        
        can_generate = url_valid and groq_api_key and st.session_state.stage not in ["processing"]
        
        if st.button(
            f"✨ Generate Blog Post",
            disabled=not can_generate,
            help="Start the multi-agent blog generation pipeline" if can_generate else "Enter a valid YouTube URL and API key first",
        ):
            st.session_state.stage = "processing"
            st.session_state.error = None
            st.session_state.blog_content = ""
            # Reset agent statuses
            for agent in st.session_state.agent_statuses:
                st.session_state.agent_statuses[agent] = {"status": "pending", "duration": 0, "progress": 0}
            st.rerun()
        
        if not groq_api_key:
            st.markdown('<div style="font-size: 12px; color: var(--text-muted); text-align: center; margin-top: 8px;">Enter your Groq API key above</div>', unsafe_allow_html=True)
        elif not url_valid:
            st.markdown('<div style="font-size: 12px; color: var(--text-muted); text-align: center; margin-top: 8px;">Enter a valid YouTube URL above</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<hr style="border: none; border-top: 1px solid rgba(148,163,184,0.12); margin: 0;">', unsafe_allow_html=True)
    
    # ─── WORKFLOW PROGRESS ───
    st.markdown('<div class="section-header">Workflow Progress</div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div style="padding: 0 20px 20px;">', unsafe_allow_html=True)
        
        agent_info = [
            ("Research Analyst", "🔬"),
            ("Content Strategist", "📐"),
            ("SEO Optimizer", "🔍"),
            ("Blog Writer", "✍️"),
            ("Quality Reviewer", "✅"),
        ]
        
        progress_html = '<div class="agent-progress-container">'
        for agent_name, icon in agent_info:
            ag = st.session_state.agent_statuses.get(agent_name, {"status": "pending", "duration": 0})
            status = ag["status"]
            duration = ag.get("duration", 0)
            
            if status == "pending":
                dot = '<span class="agent-dot agent-dot-pending"></span>'
                status_text = '<span style="color: var(--text-dim); font-size: 11px;">Pending</span>'
            elif status == "active":
                dot = '<span class="agent-dot agent-dot-active"></span>'
                status_text = '<span style="color: var(--accent-cyan); font-size: 11px;">Working...</span>'
            else:
                dot = '<span class="agent-dot agent-dot-complete"></span>'
                status_text = f'<span style="color: var(--accent-emerald); font-size: 11px;">✓ {duration}s</span>'
            
            progress_html += f"""
            <div class="agent-progress-item">
              <div style="display: flex; align-items: center;">
                {dot}
                <span class="agent-name">{icon} {agent_name}</span>
              </div>
              {status_text}
            </div>
            """
        
        progress_html += '</div>'
        st.markdown(progress_html, unsafe_allow_html=True)
        
        # Overall progress bar
        completed = sum(1 for ag in st.session_state.agent_statuses.values() if ag["status"] == "complete")
        total = len(st.session_state.agent_statuses)
        if completed > 0:
            pct = int((completed / total) * 100)
            st.markdown(f"""
            <div style="margin-top: 12px;">
              <div style="display: flex; justify-content: space-between; font-size: 11px; color: var(--text-muted); margin-bottom: 4px;">
                <span>Overall Progress</span>
                <span>{pct}%</span>
              </div>
              <div class="progress-bar-container">
                <div class="progress-bar-fill" style="width: {pct}%;"></div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div style="padding: 16px 20px; border-top: 1px solid rgba(148,163,184,0.12);">
      <div style="font-size: 11px; color: var(--text-dim); text-align: center; line-height: 1.6;">
        DocMind Studio v2.0<br>
        5-Agent CrewAI Pipeline
      </div>
    </div>
    """, unsafe_allow_html=True)


# ============================
# MAIN CONTENT AREA
# ============================

# ─── STAGE: INPUT ───
if st.session_state.stage == "input":
    
    if st.session_state.error:
        st.markdown(f"""
        <div class="error-card">
          <div class="error-icon">⚠️</div>
          <div class="error-title">Something went wrong</div>
          <div class="error-message">{st.session_state.error}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="hero-state">
      <span class="hero-icon">✨</span>
      <div class="hero-title">Transform Videos into Blog Posts</div>
      <div class="hero-subtitle">
        Paste a YouTube URL in the sidebar to automatically convert video content 
        into SEO-optimized, publication-ready blog posts using 5 specialized AI agents.
      </div>
      <div style="display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; margin-top: 32px;">
        <div style="background: rgba(236,72,153,0.1); border: 1px solid rgba(236,72,153,0.2); border-radius: 12px; padding: 16px 24px; text-align: center;">
          <div style="font-size: 24px; margin-bottom: 6px;">🔬</div>
          <div style="font-family: var(--font-ui); font-size: 13px; color: var(--text-secondary); font-weight: 500;">Research Agent</div>
          <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">Analyzes content depth</div>
        </div>
        <div style="background: rgba(168,85,247,0.1); border: 1px solid rgba(168,85,247,0.2); border-radius: 12px; padding: 16px 24px; text-align: center;">
          <div style="font-size: 24px; margin-bottom: 6px;">📐</div>
          <div style="font-family: var(--font-ui); font-size: 13px; color: var(--text-secondary); font-weight: 500;">Strategy Agent</div>
          <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">Structures the outline</div>
        </div>
        <div style="background: rgba(6,182,212,0.1); border: 1px solid rgba(6,182,212,0.2); border-radius: 12px; padding: 16px 24px; text-align: center;">
          <div style="font-size: 24px; margin-bottom: 6px;">🔍</div>
          <div style="font-family: var(--font-ui); font-size: 13px; color: var(--text-secondary); font-weight: 500;">SEO Agent</div>
          <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">Optimizes for search</div>
        </div>
        <div style="background: rgba(236,72,153,0.08); border: 1px solid rgba(236,72,153,0.15); border-radius: 12px; padding: 16px 24px; text-align: center;">
          <div style="font-size: 24px; margin-bottom: 6px;">✍️</div>
          <div style="font-family: var(--font-ui); font-size: 13px; color: var(--text-secondary); font-weight: 500;">Writer Agent</div>
          <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">Writes full content</div>
        </div>
        <div style="background: rgba(16,185,129,0.08); border: 1px solid rgba(16,185,129,0.2); border-radius: 12px; padding: 16px 24px; text-align: center;">
          <div style="font-size: 24px; margin-bottom: 6px;">✅</div>
          <div style="font-family: var(--font-ui); font-size: 13px; color: var(--text-secondary); font-weight: 500;">Review Agent</div>
          <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">Polishes to publish</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(get_stage_bar_html(0), unsafe_allow_html=True)


# ─── STAGE: PROCESSING ───
elif st.session_state.stage == "processing":
    
    agent_names = [
        ("Research Analyst", "🔬", ["Analyzing video structure...", "Extracting key concepts...", "Identifying main arguments...", "Detecting important topics..."]),
        ("Content Strategist", "📐", ["Organizing research findings...", "Creating blog outline...", "Designing section hierarchy...", "Planning content flow..."]),
        ("SEO Optimizer", "🔍", ["Generating SEO title...", "Writing meta description...", "Finding primary keyword...", "Building keyword strategy..."]),
        ("Blog Writer", "✍️", ["Writing introduction...", "Developing main sections...", "Adding examples and detail...", "Crafting conclusion and CTA..."]),
        ("Quality Reviewer", "✅", ["Checking grammar and style...", "Eliminating redundancy...", "Verifying tone consistency...", "Final polish and review..."]),
    ]
    
    # Show stage header
    st.markdown("""
    <div style="margin-bottom: 24px;">
      <div style="font-family: var(--font-display); font-size: 28px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px;">
        🤖 Multi-Agent Pipeline Running
      </div>
      <div style="font-family: var(--font-ui); font-size: 15px; color: var(--text-secondary);">
        5 specialized AI agents are collaborating to transform your video into a blog post
      </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Transcript extraction first
    with st.spinner(""):
        st.markdown("""
        <div style="background: var(--color-surface-1); border: 1px solid rgba(6,182,212,0.3); border-radius: 12px; padding: 16px 20px; margin-bottom: 16px; display: flex; align-items: center; gap: 12px;">
          <span style="font-size: 20px;">📥</span>
          <div>
            <div style="font-family: var(--font-ui); font-size: 14px; font-weight: 600; color: var(--text-primary);">Extracting transcript from YouTube...</div>
            <div style="font-size: 12px; color: var(--text-muted);">Fetching captions and timestamps</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Fetch transcript
        success, formatted, raw, err_msg = fetch_transcript(st.session_state.video_id)
        
        if not success:
            st.session_state.stage = "input"
            st.session_state.error = err_msg
            st.rerun()
        
        st.session_state.transcript_formatted = formatted
        st.session_state.transcript_raw = raw
    
    # Show agent cards with real pipeline execution
    agent_container = st.container()
    
    with agent_container:
        # Show all cards initially as pending
        placeholders = {}
        for i, (name, icon, tasks) in enumerate(agent_names):
            placeholders[name] = st.empty()
            placeholders[name].markdown(
                get_agent_card_html(name, icon, "pending", [], 0),
                unsafe_allow_html=True
            )
        
        # Stage progress bar
        stage_placeholder = st.empty()
        stage_placeholder.markdown(get_stage_bar_html(1), unsafe_allow_html=True)
        
        # Run actual pipeline
        try:
            from agents import run_agent_pipeline
            
            raw_to_process = chunk_transcript(st.session_state.transcript_raw, max_words=7000)
            
            # Track timing
            gen_start = time.time()
            
            def on_agent_start(idx, name):
                agent_key = list(st.session_state.agent_statuses.keys())[idx]
                st.session_state.agent_statuses[agent_key]["status"] = "active"
                st.session_state.agent_statuses[agent_key]["progress"] = 0
                
                _, icon, tasks = agent_names[idx]
                placeholders[name].markdown(
                    get_agent_card_html(name, icon, "active", tasks[:2], 30),
                    unsafe_allow_html=True
                )
                stage_placeholder.markdown(get_stage_bar_html(idx + 1), unsafe_allow_html=True)
            
            def on_agent_complete(idx, name, duration):
                agent_key = list(st.session_state.agent_statuses.keys())[idx]
                st.session_state.agent_statuses[agent_key]["status"] = "complete"
                st.session_state.agent_statuses[agent_key]["duration"] = duration
                st.session_state.agent_statuses[agent_key]["progress"] = 100
                
                _, icon, tasks = agent_names[idx]
                placeholders[name].markdown(
                    get_agent_card_html(name, icon, "complete", tasks, 100, duration),
                    unsafe_allow_html=True
                )
            
            result = run_agent_pipeline(
                api_key=groq_api_key,
                transcript=raw_to_process,
                tone=tone,
                word_count=word_count_target,
                seo_mode=seo_mode,
                progress_callbacks={
                    "on_agent_start": on_agent_start,
                    "on_agent_complete": on_agent_complete,
                }
            )
            
            st.session_state.blog_content = result["blog_content"]
            st.session_state.seo_metadata = parse_blog_metadata(result["blog_content"])
            st.session_state.generation_time = round(time.time() - gen_start, 1)
            st.session_state.stage = "output"
            st.rerun()
            
        except Exception as e:
            err_str = str(e)
            if "rate" in err_str.lower() or "429" in err_str:
                st.session_state.error = "⏱ Rate limit reached. Please wait 60 seconds and try again. Groq free tier allows 30 requests/minute."
            elif "invalid" in err_str.lower() and "api" in err_str.lower():
                st.session_state.error = "🔑 Invalid API key. Please check your Groq API key and try again."
            elif "token" in err_str.lower() and "limit" in err_str.lower():
                st.session_state.error = "📄 Video is too long for the free tier. Try a shorter video (under 30 minutes)."
            else:
                st.session_state.error = f"Generation failed: {err_str[:200]}. Please try again."
            
            st.session_state.stage = "input"
            st.rerun()


# ─── STAGE: OUTPUT ───
elif st.session_state.stage == "output":
    
    blog = st.session_state.blog_content
    meta = st.session_state.seo_metadata
    wc = count_words(blog)
    
    # Header
    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px;">
      <div>
        <div style="font-family: var(--font-display); font-size: 28px; font-weight: 600; color: var(--text-primary); margin-bottom: 4px;">
          📝 Blog Post Generated
        </div>
        <div style="font-family: var(--font-ui); font-size: 14px; color: var(--text-muted);">
          {format_word_count(wc)} · {tone} Tone · {seo_mode} SEO · Generated in {st.session_state.generation_time}s
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    
    # SEO Metadata Section
    st.markdown(get_seo_section_html(
        meta.get("seo_title", ""),
        meta.get("meta_description", ""),
        meta.get("primary_keyword", ""),
        meta.get("secondary_keywords", []),
    ), unsafe_allow_html=True)
    
    # Blog Divider
    st.markdown('<hr class="blog-divider">', unsafe_allow_html=True)
    
    # Blog Content with Newsreader typography
    clean_blog = clean_blog_for_display(blog)
    blog_html = md.markdown(clean_blog, extensions=['fenced_code', 'tables'])
    
    st.markdown(f"""
    <div class="blog-output-card">
      <div class="blog-content">
        {blog_html}
      </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Stage Bar
    st.markdown(get_stage_bar_html(5), unsafe_allow_html=True)
    
    # Export Section
    st.markdown("""
    <div style="margin-top: 32px;">
      <div class="sidebar-label" style="padding: 0; margin-bottom: 12px;">Export Your Blog Post</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.download_button(
            label="⬇ Download Markdown (.md)",
            data=blog,
            file_name=f"docmind-blog-{st.session_state.video_id}.md",
            mime="text/markdown",
        )
    
    with col2:
        st.download_button(
            label="⬇ Download Text (.txt)",
            data=clean_blog,
            file_name=f"docmind-blog-{st.session_state.video_id}.txt",
            mime="text/plain",
        )
    
    with col3:
        st.download_button(
            label="⬇ Download HTML (.html)",
            data=f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{meta.get('seo_title', 'Blog Post')}</title>
  <meta name="description" content="{meta.get('meta_description', '')}">
  <style>
    body {{ max-width: 800px; margin: 60px auto; font-family: 'Georgia', serif; font-size: 18px; line-height: 1.8; color: #1a1a1a; padding: 0 20px; }}
    h1 {{ font-size: 36px; }} h2 {{ font-size: 28px; }} h3 {{ font-size: 22px; }}
    pre {{ background: #f4f4f4; padding: 16px; border-radius: 8px; overflow-x: auto; }}
    code {{ background: #f0f0f0; padding: 2px 6px; border-radius: 4px; font-size: 14px; }}
    blockquote {{ border-left: 3px solid #ec4899; padding: 12px 20px; background: #fafafa; }}
  </style>
</head>
<body>
{blog_html}
</body>
</html>""",
            file_name=f"docmind-blog-{st.session_state.video_id}.html",
            mime="text/html",
        )
    
    # Copy to clipboard (using text_area trick)
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📋 Copy to Clipboard"):
        st.code(blog, language=None)
    
    # Generate Another
    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns([3, 1])
    with col_right:
        if st.button("🔄 Generate Another", help="Reset and start with a new video"):
            st.session_state.stage = "input"
            st.session_state.url = ""
            st.session_state.video_id = None
            st.session_state.blog_content = ""
            st.session_state.transcript_formatted = ""
            st.session_state.transcript_raw = ""
            st.session_state.seo_metadata = {}
            st.session_state.error = None
            for agent in st.session_state.agent_statuses:
                st.session_state.agent_statuses[agent] = {"status": "pending", "duration": 0, "progress": 0}
            st.rerun()
