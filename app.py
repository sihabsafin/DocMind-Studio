"""
DocMind Studio — Main Application
YouTube to Blog Automation Platform
Built with Streamlit + Groq (Direct API)

NEW FEATURES v3.0:
  1. Animated typewriter effect on blog output
  2. Floating sticky action bar (Copy | Download | Split View | Regenerate)
  3. Split View Mode — raw markdown left, rendered preview right
  4. Agent Thought Bubbles — live "thinking" excerpts during processing
  5. Confetti on completion
  6. Progress time estimate with live elapsed timer
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

# ── NEW FEATURE CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Typewriter animation ── */
@keyframes typewriter-cursor {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0; }
}
.typewriter-cursor {
  display: inline-block;
  width: 2px;
  height: 1.1em;
  background: #ec4899;
  margin-left: 3px;
  vertical-align: text-bottom;
  animation: typewriter-cursor 0.8s ease infinite;
}

/* ── Floating action bar ── */
.floating-bar {
  position: fixed;
  top: 64px;
  right: 24px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.fab-btn {
  background: rgba(26,35,50,0.95);
  border: 1px solid rgba(236,72,153,0.35);
  border-radius: 10px;
  padding: 10px 16px;
  color: #f1f5f9;
  font-family: Inter, sans-serif;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  backdrop-filter: blur(12px);
  transition: all 200ms ease;
  display: flex;
  align-items: center;
  gap: 7px;
  white-space: nowrap;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
.fab-btn:hover {
  background: rgba(236,72,153,0.18);
  border-color: #ec4899;
  transform: translateX(-3px);
}

/* ── Agent thought bubble ── */
.thought-bubble {
  background: rgba(168,85,247,0.08);
  border: 1px solid rgba(168,85,247,0.25);
  border-radius: 10px;
  padding: 10px 14px;
  margin-top: 10px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: #a855f7;
  line-height: 1.6;
  position: relative;
  animation: fadeIn 0.4s ease;
}
.thought-bubble::before {
  content: '💭 Thinking...';
  display: block;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #7c3aed;
  margin-bottom: 5px;
}

/* ── Confetti canvas ── */
#confetti-canvas {
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 100%;
  pointer-events: none;
  z-index: 99999;
}

/* ── Timer badge ── */
.timer-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(6,182,212,0.12);
  border: 1px solid rgba(6,182,212,0.3);
  border-radius: 20px;
  padding: 5px 14px;
  font-family: Inter, sans-serif;
  font-size: 13px;
  color: #06b6d4;
  font-weight: 500;
}
.timer-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: #06b6d4;
  animation: pulse-dot 1.2s ease infinite;
}
.eta-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(245,158,11,0.1);
  border: 1px solid rgba(245,158,11,0.25);
  border-radius: 20px;
  padding: 5px 14px;
  font-family: Inter, sans-serif;
  font-size: 12px;
  color: #f59e0b;
}

/* ── Split view ── */
.split-left {
  background: #0f1929;
  border: 1px solid rgba(148,163,184,0.1);
  border-radius: 12px;
  padding: 24px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  color: #94a3b8;
  line-height: 1.8;
  height: 600px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
}
.split-right {
  background: #1a2332;
  border: 1px solid rgba(148,163,184,0.12);
  border-radius: 12px;
  padding: 32px;
  font-family: 'Newsreader', Georgia, serif;
  font-size: 16px;
  color: #f1f5f9;
  line-height: 1.8;
  height: 600px;
  overflow-y: auto;
}

/* ── Success celebration ── */
.success-ring {
  width: 90px; height: 90px;
  border-radius: 50%;
  background: linear-gradient(135deg, #10b981, #06b6d4);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  margin: 0 auto 20px;
  animation: slideUp 0.5s ease, glow-pulse 2s ease infinite;
  box-shadow: 0 0 30px rgba(16,185,129,0.4);
}

/* ── Progress time bar ── */
.progress-time-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
</style>
""", unsafe_allow_html=True)

# ── Confetti JS ──────────────────────────────────────────────────────────────
CONFETTI_JS = """
<canvas id="confetti-canvas"></canvas>
<script>
(function(){
  var canvas = document.getElementById('confetti-canvas');
  var ctx = canvas.getContext('2d');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  var pieces = [];
  var colors = ['#ec4899','#a855f7','#06b6d4','#10b981','#f59e0b','#f1f5f9'];
  var total = 160;

  for(var i = 0; i < total; i++){
    pieces.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height - canvas.height,
      r: Math.random() * 8 + 4,
      d: Math.random() * total + 10,
      color: colors[Math.floor(Math.random() * colors.length)],
      tilt: Math.floor(Math.random() * 10) - 10,
      tiltAngle: 0,
      tiltAngleInc: (Math.random() * 0.07) + 0.05
    });
  }

  var angle = 0;
  var frames = 0;
  var maxFrames = 200;

  function draw(){
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    angle += 0.01;
    frames++;
    pieces.forEach(function(p, i){
      p.tiltAngle += p.tiltAngleInc;
      p.y += (Math.cos(angle + p.d) + 2 + p.r/8);
      p.x += Math.sin(angle);
      p.tilt = Math.sin(p.tiltAngle) * 12;
      ctx.beginPath();
      ctx.lineWidth = p.r / 2;
      ctx.strokeStyle = p.color;
      ctx.moveTo(p.x + p.tilt + p.r/4, p.y);
      ctx.lineTo(p.x + p.tilt, p.y + p.tilt + p.r/4);
      ctx.stroke();
      if(p.y > canvas.height + 20) {
        p.y = -20;
        p.x = Math.random() * canvas.width;
      }
    });
    if(frames < maxFrames) requestAnimationFrame(draw);
    else { ctx.clearRect(0,0,canvas.width,canvas.height); }
  }
  draw();
})();
</script>
"""

# ── API Key ──────────────────────────────────────────────────────────────────
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
        "agent_thoughts": {},
        "error": None,
        "generation_time": 0,
        "tone": "Professional",
        "length_label": "Medium (~1500 words)",
        "advanced_seo": False,
        "seo_mode": "Basic",
        "word_count_target": 1500,
        "split_view": False,
        "show_confetti": False,
        "processing_start": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_state()

# ── TOP BAR ──────────────────────────────────────────────────────────────────
api_dot   = "#10b981" if GROQ_API_KEY else "#f43f5e"
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
    video_id  = None

    if url_input:
        st.session_state.url = url_input
        is_valid, result = validate_youtube_url(url_input)
        if is_valid:
            url_valid = True
            video_id  = result
            st.session_state.video_id = video_id
            st.success(f"✓ Valid URL — Video ID: `{video_id}`")
        elif result:
            st.error(result)

    st.divider()

    st.markdown(
        '<p style="font-family:Inter,sans-serif;font-size:10px;font-weight:600;'
        'letter-spacing:0.15em;text-transform:uppercase;color:#64748b;'
        'padding:8px 4px;margin:0;">CUSTOMIZATION</p>',
        unsafe_allow_html=True,
    )

    tone = st.selectbox(
        "Writing Tone",
        ["Professional", "Casual", "Educational", "Storytelling", "Technical"],
        index=["Professional","Casual","Educational","Storytelling","Technical"].index(
            st.session_state.tone),
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
    )
    st.session_state.length_label      = length_label
    st.session_state.word_count_target = length_options[length_label]

    advanced_seo = st.checkbox(
        "Advanced SEO Mode",
        value=st.session_state.advanced_seo,
        help="Adds secondary keywords, heading suggestions, keyword density & link opportunities",
    )
    st.session_state.advanced_seo = advanced_seo
    st.session_state.seo_mode     = "Advanced" if advanced_seo else "Basic"

    st.divider()

    can_generate = url_valid and bool(GROQ_API_KEY) and st.session_state.stage != "processing"

    # ── FEATURE 6: ETA display under generate button ──────────────────────
    eta_map = {800: 35, 1500: 55, 2500: 90, 4000: 140}
    eta_sec = eta_map.get(st.session_state.word_count_target, 55)

    if st.session_state.stage == "processing" and st.session_state.processing_start:
        elapsed = int(time.time() - st.session_state.processing_start)
        remaining = max(0, eta_sec - elapsed)
        st.markdown(f"""
<div class="progress-time-row">
  <div class="timer-badge">
    <span class="timer-dot"></span> {elapsed}s elapsed
  </div>
  <div class="eta-badge">⏳ ~{remaining}s remaining</div>
</div>
""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
<div style="margin-bottom:8px;">
  <div class="eta-badge">⏱ Est. ~{eta_sec}s for {length_label.split('(')[0].strip()}</div>
</div>
""", unsafe_allow_html=True)

    if st.button(
        "✨  Generate Blog Post",
        disabled=not can_generate,
        use_container_width=True,
        help=(
            "Start the 5-agent blog generation pipeline" if can_generate
            else ("Add GROQ_API_KEY to secrets.toml" if not GROQ_API_KEY
                  else "Enter a valid YouTube URL first")
        ),
    ):
        st.session_state.stage            = "processing"
        st.session_state.error            = None
        st.session_state.blog_content     = ""
        st.session_state.show_confetti    = False
        st.session_state.agent_thoughts   = {}
        st.session_state.processing_start = time.time()
        for agent in st.session_state.agent_statuses:
            st.session_state.agent_statuses[agent] = {"status": "pending", "duration": 0}
        st.rerun()

    if not GROQ_API_KEY:
        st.caption("🔑 Add GROQ_API_KEY to secrets.toml")
    elif not url_valid:
        st.caption("Paste a YouTube URL above to get started")

    st.divider()

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

    rows_html = ""
    for agent_name, icon in agent_info:
        ag       = st.session_state.agent_statuses.get(agent_name, {"status":"pending","duration":0})
        status   = ag["status"]
        duration = ag.get("duration", 0)
        if status == "active":
            dot_color = "#06b6d4"; dot_anim = "animation:pulse-dot 1.5s ease infinite;"
            st_html   = '<span style="color:#06b6d4;font-size:11px;">Working…</span>'
        elif status == "complete":
            dot_color = "#10b981"; dot_anim = ""
            st_html   = f'<span style="color:#10b981;font-size:11px;">✓ {duration}s</span>'
        else:
            dot_color = "#475569"; dot_anim = ""
            st_html   = '<span style="color:#475569;font-size:11px;">Pending</span>'

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
          {st_html}
        </div>"""

    st.markdown(rows_html, unsafe_allow_html=True)

    completed = sum(1 for ag in st.session_state.agent_statuses.values() if ag["status"] == "complete")
    total     = len(st.session_state.agent_statuses)
    if completed > 0:
        pct = int((completed / total) * 100)
        st.markdown(f"""
<div style="margin-top:12px;">
  <div style="display:flex;justify-content:space-between;font-size:11px;color:#64748b;margin-bottom:4px;">
    <span>Overall Progress</span><span>{pct}%</span>
  </div>
  <div style="background:#2d4158;border-radius:4px;height:4px;overflow:hidden;">
    <div style="width:{pct}%;height:100%;
                background:linear-gradient(90deg,#ec4899,#a855f7,#06b6d4);
                border-radius:4px;transition:width 0.5s ease;"></div>
  </div>
</div>""", unsafe_allow_html=True)

    st.markdown(
        '<p style="font-size:11px;color:#475569;text-align:center;margin-top:20px;">'
        'DocMind Studio v3.0 · 5-Agent Groq Pipeline</p>',
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════
# MAIN CONTENT
# ════════════════════════════════════════════════════════

# ── STAGE: INPUT ─────────────────────────────────────────────────────────────
if st.session_state.stage == "input":

    if st.session_state.error:
        err_html       = st.session_state.error.replace("\n\n","<br><br>").replace("\n","<br>")
        is_no_captions = any(k in st.session_state.error.lower() for k in
                             ["no captions","no transcript","has no captions"])
        is_ip_block = any(k in st.session_state.error.lower() for k in
                          ["blocking transcript","ip address","webshare","cloud platform","run locally"])
        extra_panel = ""
        if is_ip_block:
            extra_panel = """
<div style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.3);
     border-radius:10px;padding:18px 20px;margin-top:14px;">
  <div style="font-size:13px;font-weight:600;color:#f59e0b;margin-bottom:12px;">
    Two ways to fix this:
  </div>
  <div style="margin-bottom:14px;">
    <div style="font-size:13px;font-weight:600;color:#f1f5f9;margin-bottom:4px;">
      Option 1 — Run locally (free, works right now)
    </div>
    <div style="background:#0f1929;border-radius:8px;padding:10px 14px;
         font-family:'JetBrains Mono',monospace;font-size:12px;color:#06b6d4;margin-top:6px;">
      streamlit run app.py
    </div>
    <div style="font-size:12px;color:#64748b;margin-top:6px;">
      Your local machine has a residential IP — YouTube won't block it.
    </div>
  </div>
  <div>
    <div style="font-size:13px;font-weight:600;color:#f1f5f9;margin-bottom:4px;">
      Option 2 — Add Webshare residential proxy (~$3/mo)
    </div>
    <div style="font-size:12px;color:#94a3b8;line-height:1.7;margin-top:4px;">
      1. Sign up at <strong style="color:#f59e0b;">webshare.io</strong> → purchase a <strong>Residential</strong> plan<br>
      2. Add to <code style="background:#1a2332;padding:2px 6px;border-radius:4px;">.streamlit/secrets.toml</code>:<br>
      <span style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#06b6d4;
            display:block;background:#0f1929;padding:8px 12px;border-radius:6px;margin:6px 0;">
        WEBSHARE_USERNAME = "your-username"<br>
        WEBSHARE_PASSWORD = "your-password"
      </span>
      3. Redeploy — DocMind detects credentials and routes all requests through Webshare automatically.
    </div>
  </div>
</div>"""
        elif is_no_captions:
            extra_panel = """
<div style="background:rgba(6,182,212,0.08);border:1px solid rgba(6,182,212,0.25);
     border-radius:10px;padding:16px 20px;margin-top:14px;">
  <div style="font-size:13px;font-weight:600;color:#06b6d4;margin-bottom:10px;">
    🎬 Videos that work great with DocMind Studio:
  </div>
  <div style="display:flex;flex-wrap:wrap;gap:8px;">
    <a href="https://www.youtube.com/@Fireship" target="_blank"
       style="background:#1a2332;border:1px solid rgba(148,163,184,0.2);border-radius:6px;
              padding:5px 12px;font-size:12px;color:#cbd5e1;text-decoration:none;">🔥 Fireship</a>
    <a href="https://www.youtube.com/@lexfridman" target="_blank"
       style="background:#1a2332;border:1px solid rgba(148,163,184,0.2);border-radius:6px;
              padding:5px 12px;font-size:12px;color:#cbd5e1;text-decoration:none;">🎙 Lex Fridman</a>
    <a href="https://www.youtube.com/@NetworkChuck" target="_blank"
       style="background:#1a2332;border:1px solid rgba(148,163,184,0.2);border-radius:6px;
              padding:5px 12px;font-size:12px;color:#cbd5e1;text-decoration:none;">🌐 NetworkChuck</a>
    <a href="https://www.youtube.com/@mkbhd" target="_blank"
       style="background:#1a2332;border:1px solid rgba(148,163,184,0.2);border-radius:6px;
              padding:5px 12px;font-size:12px;color:#cbd5e1;text-decoration:none;">📱 MKBHD</a>
    <a href="https://www.youtube.com/@Kurzgesagt" target="_blank"
       style="background:#1a2332;border:1px solid rgba(148,163,184,0.2);border-radius:6px;
              padding:5px 12px;font-size:12px;color:#cbd5e1;text-decoration:none;">🌍 Kurzgesagt</a>
    <a href="https://www.youtube.com/@TED" target="_blank"
       style="background:#1a2332;border:1px solid rgba(148,163,184,0.2);border-radius:6px;
              padding:5px 12px;font-size:12px;color:#cbd5e1;text-decoration:none;">💡 TED</a>
  </div>
  <div style="font-size:11px;color:#64748b;margin-top:10px;">
    💡 Tip: On YouTube, check the <strong style="color:#94a3b8;">CC</strong> button — if visible, DocMind can process it.
  </div>
</div>"""

        st.markdown(f"""
<div style="background:rgba(26,35,50,1);border:1px solid rgba(148,163,184,0.12);
     border-left:3px solid #f43f5e;border-radius:12px;padding:20px;margin-bottom:24px;">
  <div style="font-size:22px;margin-bottom:8px;">⚠️</div>
  <div style="font-family:Inter,sans-serif;font-size:15px;font-weight:600;
              color:#f1f5f9;margin-bottom:10px;">Could Not Process This Video</div>
  <div style="font-family:Inter,sans-serif;font-size:13px;color:#cbd5e1;line-height:1.7;">{err_html}</div>
  {extra_panel}
</div>""", unsafe_allow_html=True)

    st.markdown("""
<div style="background:linear-gradient(135deg,rgba(236,72,153,0.12) 0%,rgba(168,85,247,0.07) 50%,transparent 100%);
     border-radius:24px;padding:64px 40px;text-align:center;margin-bottom:20px;">
  <div style="font-size:60px;animation:float 4s ease-in-out infinite;display:block;margin-bottom:20px;">✨</div>
  <div style="font-family:'Bricolage Grotesque',sans-serif;font-size:38px;font-weight:600;
              color:#f1f5f9;margin-bottom:16px;line-height:1.2;">Transform Videos into Blog Posts</div>
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
</div>""", unsafe_allow_html=True)

    st.markdown(get_stage_bar_html(0), unsafe_allow_html=True)


# ── STAGE: PROCESSING ─────────────────────────────────────────────────────────
elif st.session_state.stage == "processing":

    # ── FEATURE 4: Agent thought bubble snippets ──────────────────────────
    AGENT_THOUGHTS = {
        "Research Analyst": [
            "Parsing transcript structure… identified 4 key topic clusters",
            "Found 3 strong supporting arguments in the content",
            "Detected chronological flow — good for narrative outline",
            "Extracting data points and examples from transcript…",
        ],
        "Content Strategist": [
            "Designing H2 hierarchy… planning 5 main sections",
            "Crafting attention hook for the introduction…",
            "Building logical transition bridges between sections",
            "Optimizing content flow for reader engagement…",
        ],
        "SEO Optimizer": [
            "Analyzing search intent for target keyword cluster…",
            "Drafting title variants — checking character limits (60 max)",
            "Identifying long-tail keyword opportunities…",
            "Writing meta description with primary CTA embedded",
        ],
        "Blog Writer": [
            "Opening with a compelling hook sentence…",
            "Weaving keywords naturally into paragraph flow…",
            "Adding concrete examples and actionable insights…",
            "Crafting the call-to-action with urgency and clarity",
        ],
        "Quality Reviewer": [
            "Scanning for passive voice and weak phrasing…",
            "Checking keyword density — adjusting for naturalness",
            "Improving sentence variety in paragraphs 3 and 7…",
            "Final readability pass — Flesch score looks good ✓",
        ],
    }

    agent_defs = [
        ("Research Analyst",   "🔬", ["Analyzing video structure…","Extracting key concepts…","Identifying main arguments…","Detecting important topics…"]),
        ("Content Strategist", "📐", ["Organizing research findings…","Creating blog outline…","Designing section hierarchy…","Planning content flow…"]),
        ("SEO Optimizer",      "🔍", ["Generating SEO title…","Writing meta description…","Finding primary keyword…","Building keyword strategy…"]),
        ("Blog Writer",        "✍️", ["Writing introduction…","Developing main sections…","Adding examples…","Crafting conclusion and CTA…"]),
        ("Quality Reviewer",   "✅", ["Checking grammar and style…","Eliminating redundancy…","Verifying tone consistency…","Final polish…"]),
    ]

    # Header with live timer
    elapsed_now = int(time.time() - st.session_state.processing_start) if st.session_state.processing_start else 0
    eta_map2    = {800: 35, 1500: 55, 2500: 90, 4000: 140}
    eta_total   = eta_map2.get(st.session_state.word_count_target, 55)
    remain      = max(0, eta_total - elapsed_now)

    st.markdown(f"""
<div style="margin-bottom:20px;">
  <div style="font-family:'Bricolage Grotesque',sans-serif;font-size:26px;font-weight:600;
              color:#f1f5f9;margin-bottom:12px;">🤖 Multi-Agent Pipeline Running</div>
  <div class="progress-time-row">
    <div class="timer-badge"><span class="timer-dot"></span> {elapsed_now}s elapsed</div>
    <div class="eta-badge">⏳ ~{remain}s remaining</div>
    <div style="font-size:13px;color:#64748b;">5 agents collaborating in sequence</div>
  </div>
</div>""", unsafe_allow_html=True)

    # Transcript fetch
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
</div>""", unsafe_allow_html=True)

    success, formatted, raw, err_msg = fetch_transcript(st.session_state.video_id)
    transcript_ph.empty()

    if not success:
        st.session_state.stage = "input"
        st.session_state.error = err_msg
        st.rerun()

    st.session_state.transcript_formatted = formatted
    st.session_state.transcript_raw       = raw

    # Agent card placeholders + thought bubble placeholders
    placeholders       = {name: st.empty() for name, _, _ in agent_defs}
    thought_holders    = {name: st.empty() for name, _, _ in agent_defs}

    for name, icon, _ in agent_defs:
        placeholders[name].markdown(
            get_agent_card_html(name, icon, "pending", [], 0),
            unsafe_allow_html=True,
        )

    stage_ph = st.empty()
    stage_ph.markdown(get_stage_bar_html(1), unsafe_allow_html=True)

    import random

    def show_thought(name):
        """Show a random thought bubble for the active agent."""
        thoughts = AGENT_THOUGHTS.get(name, [])
        if thoughts:
            thought = random.choice(thoughts)
            thought_holders[name].markdown(
                f'<div class="thought-bubble">{thought}</div>',
                unsafe_allow_html=True,
            )

    try:
        from agents import run_agent_pipeline

        raw_to_process = chunk_transcript(st.session_state.transcript_raw, max_words=7000)
        gen_start      = time.time()

        def on_agent_start(idx, name):
            ag_key = list(st.session_state.agent_statuses.keys())[idx]
            st.session_state.agent_statuses[ag_key]["status"] = "active"
            _, icon, tasks = agent_defs[idx]
            placeholders[name].markdown(
                get_agent_card_html(name, icon, "active", tasks[:2], 35),
                unsafe_allow_html=True,
            )
            show_thought(name)   # ← FEATURE 4
            stage_ph.markdown(get_stage_bar_html(idx + 1), unsafe_allow_html=True)

        def on_agent_complete(idx, name, duration):
            ag_key = list(st.session_state.agent_statuses.keys())[idx]
            st.session_state.agent_statuses[ag_key]["status"]  = "complete"
            st.session_state.agent_statuses[ag_key]["duration"] = duration
            _, icon, tasks = agent_defs[idx]
            placeholders[name].markdown(
                get_agent_card_html(name, icon, "complete", tasks, 100, duration),
                unsafe_allow_html=True,
            )
            thought_holders[name].empty()   # clear thought bubble on complete

        result = run_agent_pipeline(
            api_key=GROQ_API_KEY,
            transcript=raw_to_process,
            tone=st.session_state.tone,
            word_count=st.session_state.word_count_target,
            seo_mode=st.session_state.seo_mode,
            progress_callbacks={
                "on_agent_start":    on_agent_start,
                "on_agent_complete": on_agent_complete,
            },
        )

        st.session_state.blog_content    = result["blog_content"]
        st.session_state.seo_metadata    = parse_blog_metadata(result["blog_content"])
        st.session_state.generation_time = round(time.time() - gen_start, 1)
        st.session_state.show_confetti   = True    # ← FEATURE 5 flag
        st.session_state.stage           = "output"
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


# ── STAGE: OUTPUT ─────────────────────────────────────────────────────────────
elif st.session_state.stage == "output":

    blog       = st.session_state.blog_content
    meta       = st.session_state.seo_metadata
    wc         = count_words(blog)
    tone_label = st.session_state.tone
    seo_mode   = st.session_state.seo_mode
    gen_time   = st.session_state.generation_time
    clean_blog = clean_blog_for_display(blog)
    blog_html  = md.markdown(clean_blog, extensions=['fenced_code', 'tables'])

    # ── FEATURE 5: Confetti on first load of output ────────────────────────
    if st.session_state.get("show_confetti", False):
        st.markdown(CONFETTI_JS, unsafe_allow_html=True)
        st.session_state.show_confetti = False

    # ── Success celebration header ─────────────────────────────────────────
    st.markdown(f"""
<div style="text-align:center;padding:32px 20px 24px;
     background:linear-gradient(135deg,rgba(16,185,129,0.08),rgba(6,182,212,0.06));
     border-radius:16px;margin-bottom:24px;border:1px solid rgba(16,185,129,0.2);">
  <div class="success-ring">🎉</div>
  <div style="font-family:'Bricolage Grotesque',sans-serif;font-size:28px;
              font-weight:600;color:#f1f5f9;margin-bottom:6px;">Blog Post Generated!</div>
  <div style="font-family:Inter,sans-serif;font-size:14px;color:#64748b;">
    {format_word_count(wc)} · {tone_label} Tone · {seo_mode} SEO · 
    <span style="color:#10b981;">⚡ Generated in {gen_time}s</span>
  </div>
</div>""", unsafe_allow_html=True)

    # ── FEATURE 2: Floating action bar ─────────────────────────────────────
    st.markdown(f"""
<div class="floating-bar">
  <div class="fab-btn" onclick="
    var el = document.querySelector('.blog-content-text');
    if(el){{navigator.clipboard.writeText(el.innerText);
    this.innerHTML='✅ Copied!';
    setTimeout(()=>this.innerHTML='📋 Copy',1500);}}">
    📋 Copy
  </div>
  <a class="fab-btn" href="data:text/markdown;charset=utf-8,{{}}" download="blog.md"
     style="text-decoration:none;">⬇ .md</a>
</div>""", unsafe_allow_html=True)

    # ── FEATURE 3: Split View toggle ───────────────────────────────────────
    col_hdr, col_toggle = st.columns([4, 1])
    with col_hdr:
        st.markdown("""
<div style="font-family:'Bricolage Grotesque',sans-serif;font-size:20px;
     font-weight:600;color:#f1f5f9;margin-bottom:4px;">📄 Your Blog Post</div>""",
            unsafe_allow_html=True)
    with col_toggle:
        split_mode = st.toggle("⚡ Split View", value=st.session_state.split_view,
                               help="Show raw Markdown alongside rendered preview")
        st.session_state.split_view = split_mode

    # SEO section
    st.markdown(get_seo_section_html(
        meta.get("seo_title",""),
        meta.get("meta_description",""),
        meta.get("primary_keyword",""),
        meta.get("secondary_keywords",[]),
    ), unsafe_allow_html=True)

    st.markdown("""
<hr style="border:none;height:1px;
    background:linear-gradient(90deg,#ec4899,#a855f7,transparent);margin:24px 0;">
""", unsafe_allow_html=True)

    # ── FEATURE 1: Typewriter effect + FEATURE 3: Split view ───────────────
    if split_mode:
        # Split view: raw markdown | rendered preview
        st.markdown("""
<div style="display:flex;gap:4px;margin-bottom:8px;">
  <div style="flex:1;font-size:11px;font-weight:600;letter-spacing:0.12em;
       text-transform:uppercase;color:#64748b;padding-left:4px;">
    📝 Raw Markdown
  </div>
  <div style="flex:1;font-size:11px;font-weight:600;letter-spacing:0.12em;
       text-transform:uppercase;color:#64748b;padding-left:4px;">
    👁 Rendered Preview
  </div>
</div>""", unsafe_allow_html=True)

        left_col, right_col = st.columns(2)
        with left_col:
            st.markdown(
                f'<div class="split-left">{clean_blog}</div>',
                unsafe_allow_html=True,
            )
        with right_col:
            st.markdown(
                f'<div class="split-right blog-content-text">{blog_html}</div>',
                unsafe_allow_html=True,
            )
    else:
        # ── FEATURE 1: Typewriter animation via JS ──────────────────────
        # Blog appears section by section with a smooth reveal
        sections = re.split(r'(?=\n## |\n# )', clean_blog)
        sections = [s.strip() for s in sections if s.strip()]

        st.markdown(f"""
<div style="background:#1a2332;border:1px solid rgba(148,163,184,0.12);
     border-radius:16px;padding:40px;" id="blog-output">
  <div class="blog-content-text" style="font-family:'Newsreader',Georgia,serif;
       font-size:17px;line-height:1.8;color:#f1f5f9;">
    {blog_html}
  </div>
</div>
<script>
(function(){{
  var el = document.getElementById('blog-output');
  if(!el) return;
  el.style.opacity = '0';
  el.style.transform = 'translateY(16px)';
  el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
  setTimeout(function(){{
    el.style.opacity = '1';
    el.style.transform = 'translateY(0)';
  }}, 100);

  // Animate each paragraph sequentially
  var paras = el.querySelectorAll('p, h1, h2, h3, li');
  paras.forEach(function(p, i){{
    p.style.opacity = '0';
    p.style.transform = 'translateY(10px)';
    p.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
    setTimeout(function(){{
      p.style.opacity = '1';
      p.style.transform = 'translateY(0)';
    }}, 200 + i * 40);
  }});
}})();
</script>""", unsafe_allow_html=True)

    st.markdown(get_stage_bar_html(5), unsafe_allow_html=True)

    # ── Export buttons ──────────────────────────────────────────────────────
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
        seo_title_safe = meta.get("seo_title","Blog Post").replace('"','&quot;')
        meta_desc_safe = meta.get("meta_description","").replace('"','&quot;')
        st.download_button(
            label="⬇ Download HTML (.html)",
            data=f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>{seo_title_safe}</title>
<meta name="description" content="{meta_desc_safe}">
<style>body{{max-width:800px;margin:60px auto;font-family:Georgia,serif;
font-size:18px;line-height:1.8;color:#1a1a1a;padding:0 20px}}
h1{{font-size:36px}}h2{{font-size:28px}}h3{{font-size:22px}}
pre{{background:#f4f4f4;padding:16px;border-radius:8px;overflow-x:auto}}
code{{background:#f0f0f0;padding:2px 6px;border-radius:4px}}
blockquote{{border-left:3px solid #ec4899;padding:12px 20px;background:#fafafa}}
</style></head><body>{blog_html}</body></html>""",
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
                "stage": "input", "url": "", "video_id": None,
                "blog_content": "", "transcript_formatted": "",
                "transcript_raw": "", "seo_metadata": {},
                "error": None, "show_confetti": False,
                "split_view": False, "agent_thoughts": {},
                "processing_start": None,
            })
            for agent in st.session_state.agent_statuses:
                st.session_state.agent_statuses[agent] = {"status":"pending","duration":0}
            st.rerun()
