"""
DocMind Studio — Complete CSS Design System
Pink/Purple creative automation studio aesthetic
"""

FONTS_AND_STYLES = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@400;500;600;700&family=Inter:wght@400;500;600&family=Newsreader:ital,wght@0,400;0,600;1,400&family=JetBrains+Mono&display=swap" rel="stylesheet">

<style>
/* ============================
   CSS VARIABLES
   ============================ */
:root {
  --color-void: #0a0e1a;
  --color-base: #111827;
  --color-surface-1: #1a2332;
  --color-surface-2: #243447;
  --color-surface-3: #2d4158;
  --color-glass: rgba(26,35,50,0.7);
  --color-border: rgba(148,163,184,0.12);
  --color-border-focus: rgba(236,72,153,0.4);

  --accent-pink: #ec4899;
  --accent-pink-light: #f472b6;
  --accent-pink-glow: rgba(236,72,153,0.15);
  --accent-purple: #a855f7;
  --accent-purple-glow: rgba(168,85,247,0.12);
  --accent-cyan: #06b6d4;
  --accent-cyan-glow: rgba(6,182,212,0.15);
  --accent-amber: #f59e0b;
  --accent-emerald: #10b981;
  --accent-rose: #f43f5e;

  --gradient-hero: linear-gradient(135deg, rgba(236,72,153,0.15) 0%, rgba(168,85,247,0.08) 50%, transparent 100%);
  --gradient-cta: linear-gradient(135deg, #ec4899 0%, #a855f7 100%);
  --gradient-progress: linear-gradient(90deg, #ec4899 0%, #a855f7 50%, #06b6d4 100%);

  --text-primary: #f1f5f9;
  --text-secondary: #cbd5e1;
  --text-muted: #64748b;
  --text-dim: #475569;
  --text-accent: #ec4899;

  --font-display: 'Bricolage Grotesque', 'Outfit', sans-serif;
  --font-ui: 'Inter', sans-serif;
  --font-content: 'Newsreader', 'Lora', serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
}

/* ============================
   GLOBAL RESET & BASE
   ============================ */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [class*="css"], .stApp {
  font-family: var(--font-ui) !important;
  background-color: var(--color-base) !important;
  color: var(--text-primary) !important;
}

/* ============================
   HIDE STREAMLIT CHROME
   ============================ */
#MainMenu, footer, header, .stDeployButton,
[data-testid="stToolbar"], [data-testid="stDecoration"] {
  visibility: hidden !important;
  height: 0 !important;
}

/* ============================
   SIDEBAR OVERRIDES
   ============================ */
[data-testid="stSidebar"] {
  background: var(--color-surface-2) !important;
  border-right: 1px solid var(--color-border) !important;
  width: 320px !important;
}

[data-testid="stSidebar"] > div {
  background: var(--color-surface-2) !important;
  padding: 0 !important;
}

[data-testid="stSidebarContent"] {
  padding: 0 !important;
}

/* ============================
   TEXT INPUT
   ============================ */
.stTextInput > div > div > input {
  background: var(--color-surface-1) !important;
  border: 1px solid var(--color-border) !important;
  border-radius: 12px !important;
  color: var(--text-primary) !important;
  font-family: var(--font-ui) !important;
  font-size: 14px !important;
  padding: 12px 16px !important;
  transition: all 150ms ease !important;
}

.stTextInput > div > div > input:focus {
  border: 2px solid var(--accent-pink) !important;
  box-shadow: 0 0 0 4px rgba(236,72,153,0.12) !important;
  outline: none !important;
}

.stTextInput > div > div > input::placeholder {
  color: var(--text-dim) !important;
}

/* ============================
   SELECTBOX
   ============================ */
.stSelectbox > div > div {
  background: var(--color-surface-2) !important;
  border: 1px solid var(--color-border) !important;
  border-radius: 8px !important;
  color: var(--text-primary) !important;
}

.stSelectbox > div > div:hover {
  border-color: rgba(236,72,153,0.4) !important;
}

/* ============================
   SLIDER
   ============================ */
.stSlider > div > div > div > div {
  background: var(--gradient-progress) !important;
}

.stSlider [data-baseweb="slider"] > div > div > div {
  background: var(--color-surface-3) !important;
}

/* ============================
   BUTTONS
   ============================ */
.stButton > button {
  background: var(--gradient-cta) !important;
  border: none !important;
  border-radius: 12px !important;
  color: white !important;
  font-family: var(--font-ui) !important;
  font-size: 15px !important;
  font-weight: 600 !important;
  padding: 14px 24px !important;
  width: 100% !important;
  box-shadow: 0 4px 16px rgba(236,72,153,0.3) !important;
  transition: all 200ms ease !important;
  cursor: pointer !important;
}

.stButton > button:hover {
  transform: scale(1.02) !important;
  box-shadow: 0 8px 24px rgba(236,72,153,0.4) !important;
  filter: brightness(1.1) !important;
}

.stButton > button:active {
  transform: scale(0.99) !important;
}

.stButton > button:disabled {
  background: var(--color-surface-3) !important;
  color: var(--text-dim) !important;
  box-shadow: none !important;
  transform: none !important;
  cursor: not-allowed !important;
}

/* ============================
   DOWNLOAD BUTTONS
   ============================ */
.stDownloadButton > button {
  background: var(--color-surface-2) !important;
  border: 1px solid var(--color-border) !important;
  border-radius: 8px !important;
  color: var(--text-primary) !important;
  font-family: var(--font-ui) !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  padding: 10px 18px !important;
  width: 100% !important;
  box-shadow: none !important;
  transition: all 200ms ease !important;
  text-align: left !important;
}

.stDownloadButton > button:hover {
  background: var(--color-surface-3) !important;
  border-left: 2px solid var(--accent-pink) !important;
  transform: none !important;
  box-shadow: none !important;
}

/* ============================
   CHECKBOX / TOGGLE
   ============================ */
.stCheckbox > label {
  color: var(--text-primary) !important;
  font-family: var(--font-ui) !important;
  font-size: 14px !important;
}

.stCheckbox > label > span {
  background: var(--gradient-cta) !important;
  border: none !important;
}

/* ============================
   PROGRESS BAR
   ============================ */
.stProgress > div > div > div > div {
  background: var(--gradient-progress) !important;
}

.stProgress > div > div > div {
  background: var(--color-surface-3) !important;
  border-radius: 4px !important;
}

/* ============================
   EXPANDER
   ============================ */
.streamlit-expanderHeader {
  background: var(--color-surface-1) !important;
  border: 1px solid var(--color-border) !important;
  border-radius: 8px !important;
  color: var(--text-primary) !important;
  font-family: var(--font-ui) !important;
}

.streamlit-expanderContent {
  background: var(--color-surface-1) !important;
  border: 1px solid var(--color-border) !important;
  border-top: none !important;
}

/* ============================
   LABELS
   ============================ */
.stTextInput > label, .stSelectbox > label, 
.stSlider > label, .stCheckbox > label > span:last-child {
  color: var(--text-muted) !important;
  font-family: var(--font-ui) !important;
  font-size: 11px !important;
  font-weight: 500 !important;
  letter-spacing: 0.1em !important;
  text-transform: uppercase !important;
}

/* ============================
   MARKDOWN
   ============================ */
.stMarkdown {
  color: var(--text-secondary) !important;
}

/* ============================
   SCROLLBAR
   ============================ */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--color-surface-1); }
::-webkit-scrollbar-thumb { background: var(--color-surface-3); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-pink); }

/* ============================
   ANIMATIONS
   ============================ */
@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-8px); }
}

@keyframes pulse-dot {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.3); opacity: 0.7; }
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes bounce-dots {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

@keyframes glow-pulse {
  0%, 100% { filter: drop-shadow(0 0 6px rgba(236,72,153,0.3)); }
  50% { filter: drop-shadow(0 0 12px rgba(236,72,153,0.6)); }
}

@keyframes progress-shimmer {
  0% { background-position: -100% 0; }
  100% { background-position: 200% 0; }
}

/* ============================
   COMPONENT CLASSES
   ============================ */

/* Top Bar */
.docmind-topbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(10,14,26,0.9);
  backdrop-filter: blur(24px) saturate(180%);
  border-bottom: 1px solid var(--color-border);
  padding: 12px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
}

.docmind-logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.docmind-logo-icon {
  width: 32px;
  height: 32px;
  background: var(--gradient-cta);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  animation: glow-pulse 3s ease infinite;
}

.docmind-logo-text {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.docmind-status-pill {
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: 20px;
  padding: 4px 12px;
  font-size: 12px;
  font-family: var(--font-ui);
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 6px;
}

/* Sidebar Sections */
.sidebar-section {
  padding: 20px;
  border-bottom: 1px solid var(--color-border);
}

.sidebar-label {
  font-family: var(--font-ui);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 12px;
}

/* Video Preview Card */
.video-preview-card {
  background: var(--color-surface-1);
  border: 1px solid var(--accent-emerald);
  border-radius: 8px;
  padding: 12px;
  margin-top: 8px;
  animation: slideUp 0.3s ease;
}

.video-preview-title {
  font-family: var(--font-ui);
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
  margin-bottom: 4px;
  line-height: 1.4;
}

.video-preview-meta {
  font-family: var(--font-ui);
  font-size: 11px;
  color: var(--text-muted);
}

/* URL Error */
.url-error {
  color: var(--accent-rose);
  font-family: var(--font-ui);
  font-size: 12px;
  margin-top: 6px;
}

/* URL Valid */
.url-valid {
  color: var(--accent-emerald);
  font-family: var(--font-ui);
  font-size: 12px;
  margin-top: 6px;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* Agent Progress in Sidebar */
.agent-progress-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.agent-progress-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 0;
}

.agent-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 8px;
}

.agent-dot-pending { background: var(--color-surface-3); border: 1px solid var(--text-dim); }
.agent-dot-active { background: var(--accent-cyan); animation: pulse-dot 1.5s ease infinite; }
.agent-dot-complete { background: var(--accent-emerald); }

.agent-name {
  font-family: var(--font-ui);
  font-size: 13px;
  color: var(--text-primary);
  flex: 1;
}

.agent-status-text {
  font-family: var(--font-ui);
  font-size: 11px;
  color: var(--text-muted);
}

/* Transcript Card */
.transcript-card {
  background: var(--color-surface-1);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: 28px;
  animation: slideUp 0.4s ease;
}

.transcript-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border);
}

.transcript-title {
  font-family: var(--font-ui);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--text-muted);
  border-left: 3px solid var(--accent-cyan);
  padding-left: 8px;
}

.transcript-body {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.8;
  max-height: 400px;
  overflow-y: auto;
  padding-right: 8px;
}

.transcript-timestamp {
  color: var(--accent-cyan);
  font-weight: 600;
}

.transcript-meta {
  font-family: var(--font-ui);
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border);
}

/* Agent Cards in Main Area */
.agent-card {
  background: var(--color-surface-1);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 12px;
  animation: slideUp 0.4s ease;
  transition: all 300ms ease;
}

.agent-card-active {
  border-left: 3px solid var(--accent-pink);
  box-shadow: 0 0 20px rgba(236,72,153,0.08);
}

.agent-card-complete {
  border-left: 3px solid var(--accent-emerald);
  opacity: 0.85;
}

.agent-card-pending {
  opacity: 0.5;
}

.agent-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.agent-card-title {
  font-family: var(--font-ui);
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.agent-card-status {
  font-family: var(--font-ui);
  font-size: 12px;
  color: var(--text-muted);
}

.agent-status-active { color: var(--accent-cyan); }
.agent-status-complete { color: var(--accent-emerald); }
.agent-status-pending { color: var(--text-dim); }

.agent-task-list {
  font-family: var(--font-ui);
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.8;
}

.typing-indicator {
  display: inline-flex;
  gap: 4px;
  align-items: center;
}

.typing-dot {
  width: 6px;
  height: 6px;
  background: var(--accent-cyan);
  border-radius: 50%;
  display: inline-block;
}

.typing-dot:nth-child(1) { animation: bounce-dots 1.2s ease infinite 0s; }
.typing-dot:nth-child(2) { animation: bounce-dots 1.2s ease infinite 0.2s; }
.typing-dot:nth-child(3) { animation: bounce-dots 1.2s ease infinite 0.4s; }

/* Progress Bar */
.progress-bar-container {
  background: var(--color-surface-3);
  border-radius: 4px;
  height: 4px;
  margin-top: 12px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  border-radius: 4px;
  background: var(--gradient-progress);
  background-size: 200% 100%;
  animation: progress-shimmer 2s ease infinite;
  transition: width 500ms ease;
}

/* Hero Empty State */
.hero-state {
  text-align: center;
  padding: 80px 40px;
  background: var(--gradient-hero);
  border-radius: 24px;
  animation: fadeIn 0.6s ease;
}

.hero-icon {
  font-size: 64px;
  animation: float 4s ease-in-out infinite;
  display: block;
  margin-bottom: 24px;
}

.hero-title {
  font-family: var(--font-display);
  font-size: 40px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
  line-height: 1.2;
}

.hero-subtitle {
  font-family: var(--font-ui);
  font-size: 17px;
  color: var(--text-secondary);
  max-width: 480px;
  margin: 0 auto 32px;
  line-height: 1.7;
}

/* Blog Output */
.blog-output-card {
  background: var(--color-surface-1);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: 40px;
  animation: slideUp 0.5s ease;
}

.seo-section {
  background: var(--color-surface-2);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 32px;
}

.seo-label {
  font-family: var(--font-ui);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.seo-value {
  font-family: var(--font-ui);
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.seo-title-value {
  font-family: var(--font-content);
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.blog-divider {
  height: 1px;
  background: linear-gradient(90deg, var(--accent-pink), var(--accent-purple), transparent);
  margin: 24px 0;
  border: none;
}

/* Blog Content - Newsreader Typography */
.blog-content {
  font-family: var(--font-content) !important;
  font-size: 17px !important;
  line-height: 1.8 !important;
  color: var(--text-primary) !important;
}

.blog-content h1 {
  font-family: var(--font-content);
  font-size: 32px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 24px;
  line-height: 1.3;
}

.blog-content h2 {
  font-family: var(--font-content);
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 40px 0 16px;
  line-height: 1.4;
}

.blog-content h3 {
  font-family: var(--font-content);
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 32px 0 12px;
  line-height: 1.4;
}

.blog-content p {
  margin-bottom: 20px;
  color: var(--text-secondary);
}

.blog-content ul, .blog-content ol {
  margin: 16px 0 20px 24px;
  color: var(--text-secondary);
}

.blog-content li {
  margin-bottom: 8px;
  line-height: 1.7;
}

.blog-content strong {
  color: var(--text-primary);
  font-weight: 600;
}

.blog-content em {
  font-style: italic;
  color: var(--text-secondary);
}

.blog-content code {
  font-family: var(--font-mono);
  font-size: 13px;
  background: var(--color-surface-2);
  border-radius: 4px;
  padding: 2px 6px;
  color: var(--accent-pink);
}

.blog-content pre {
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 16px;
  overflow-x: auto;
  margin: 20px 0;
}

.blog-content blockquote {
  border-left: 3px solid var(--accent-pink);
  padding: 12px 20px;
  margin: 20px 0;
  background: var(--color-surface-2);
  border-radius: 0 8px 8px 0;
  color: var(--text-secondary);
  font-style: italic;
}

/* Keyword Pills */
.keyword-pill {
  display: inline-block;
  background: rgba(236,72,153,0.12);
  border: 1px solid rgba(236,72,153,0.3);
  border-radius: 20px;
  padding: 3px 10px;
  font-size: 12px;
  color: var(--accent-pink);
  margin: 2px;
  font-family: var(--font-ui);
}

/* Stage Progression Bar */
.stage-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  padding: 20px;
  background: var(--color-surface-1);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  margin-top: 20px;
}

.stage-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.stage-dot {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  background: var(--color-surface-2);
  border: 2px solid var(--color-border);
  color: var(--text-dim);
  font-weight: 600;
  transition: all 300ms ease;
}

.stage-dot-active {
  background: var(--gradient-cta);
  border-color: transparent;
  color: white;
  transform: scale(1.1);
  box-shadow: 0 0 12px rgba(236,72,153,0.3);
}

.stage-dot-complete {
  background: var(--accent-emerald);
  border-color: transparent;
  color: white;
}

.stage-label {
  font-family: var(--font-ui);
  font-size: 11px;
  color: var(--text-muted);
  text-align: center;
}

.stage-label-active { color: var(--accent-pink); font-weight: 600; }
.stage-label-complete { color: var(--accent-emerald); }

.stage-connector {
  width: 40px;
  height: 2px;
  background: var(--color-border);
  margin: 0 4px;
  margin-bottom: 20px;
}

.stage-connector-active { background: var(--gradient-progress); }

/* Success State */
.success-state {
  text-align: center;
  padding: 60px 40px;
  animation: fadeIn 0.6s ease;
}

.success-icon {
  width: 80px;
  height: 80px;
  background: var(--accent-emerald);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  margin: 0 auto 24px;
  animation: slideUp 0.5s ease;
}

.success-title {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.success-subtitle {
  font-family: var(--font-ui);
  font-size: 16px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.success-stats {
  font-family: var(--font-ui);
  font-size: 14px;
  color: var(--text-muted);
  margin-bottom: 32px;
}

/* Error Card */
.error-card {
  background: var(--color-surface-1);
  border: 1px solid var(--color-border);
  border-left: 3px solid var(--accent-rose);
  border-radius: 12px;
  padding: 20px;
  animation: slideUp 0.3s ease;
}

.error-icon {
  font-size: 24px;
  margin-bottom: 8px;
}

.error-title {
  font-family: var(--font-ui);
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
}

.error-message {
  font-family: var(--font-ui);
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}

/* Section Headers in Sidebar */
.section-header {
  font-family: var(--font-ui);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--text-muted);
  padding: 16px 20px 8px;
}

/* Rate Limit Countdown */
.countdown-card {
  background: rgba(244,63,94,0.08);
  border: 1px solid rgba(244,63,94,0.3);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  animation: slideUp 0.3s ease;
}

.countdown-timer {
  font-family: var(--font-display);
  font-size: 48px;
  font-weight: 700;
  color: var(--accent-rose);
  margin: 8px 0;
}

</style>
"""


def get_stage_bar_html(current_stage: int) -> str:
    """Generate stage progression bar HTML"""
    stages = ["Input", "Analyze", "Structure", "Write", "Review"]
    html = '<div class="stage-bar">'
    
    for i, stage in enumerate(stages):
        if i < current_stage:
            dot_class = "stage-dot stage-dot-complete"
            label_class = "stage-label stage-label-complete"
            icon = "✓"
        elif i == current_stage:
            dot_class = "stage-dot stage-dot-active"
            label_class = "stage-label stage-label-active"
            icon = str(i + 1)
        else:
            dot_class = "stage-dot"
            label_class = "stage-label"
            icon = str(i + 1)
        
        html += f"""
        <div class="stage-step">
          <div class="{dot_class}">{icon}</div>
          <span class="{label_class}">{stage}</span>
        </div>
        """
        
        if i < len(stages) - 1:
            conn_class = "stage-connector" + (" stage-connector-active" if i < current_stage else "")
            html += f'<div class="{conn_class}" style="margin-bottom: 22px;"></div>'
    
    html += '</div>'
    return html


def get_agent_card_html(agent_name: str, icon: str, status: str, tasks: list, progress: int = 0, duration: float = 0) -> str:
    """Generate agent card HTML"""
    if status == "active":
        card_class = "agent-card agent-card-active"
        status_class = "agent-status-active"
        status_text = '<span class="typing-indicator"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></span> Working...'
    elif status == "complete":
        card_class = "agent-card agent-card-complete"
        status_class = "agent-status-complete"
        status_text = f"✓ Complete ({duration}s)"
    else:
        card_class = "agent-card agent-card-pending"
        status_class = "agent-status-pending"
        status_text = "⏸ Pending"
    
    task_html = ""
    if tasks and status in ["active", "complete"]:
        task_html = "<div class='agent-task-list'>"
        for task in tasks:
            task_html += f"<div>• {task}</div>"
        task_html += "</div>"
    
    progress_html = ""
    if status == "active":
        progress_html = f"""
        <div class="progress-bar-container" style="margin-top: 12px;">
          <div class="progress-bar-fill" style="width: {progress}%;"></div>
        </div>
        <div style="text-align: right; font-size: 11px; color: var(--text-muted); margin-top: 4px;">{progress}%</div>
        """
    
    return f"""
    <div class="{card_class}">
      <div class="agent-card-header">
        <div class="agent-card-title">{icon} {agent_name}</div>
        <div class="agent-card-status {status_class}">{status_text}</div>
      </div>
      {task_html}
      {progress_html}
    </div>
    """


def get_seo_section_html(seo_title: str, meta_desc: str, primary_kw: str, secondary_kws: list) -> str:
    """Generate SEO metadata section HTML"""
    kw_pills = ""
    if secondary_kws:
        kw_pills = "".join([f'<span class="keyword-pill">{kw}</span>' for kw in secondary_kws[:8]])
    
    return f"""
    <div class="seo-section">
      <div style="margin-bottom: 16px;">
        <div class="seo-label">SEO Title</div>
        <div class="seo-title-value">{seo_title or "Generated SEO Title"}</div>
      </div>
      <div style="margin-bottom: 16px;">
        <div class="seo-label">Meta Description</div>
        <div class="seo-value">{meta_desc or "Generated meta description"}</div>
      </div>
      <div style="margin-bottom: {'16px' if secondary_kws else '0'};">
        <div class="seo-label">Primary Keyword</div>
        <div class="seo-value"><span class="keyword-pill">{primary_kw or "AI content"}</span></div>
      </div>
      {f'<div><div class="seo-label">Secondary Keywords</div><div style="margin-top: 6px;">{kw_pills}</div></div>' if secondary_kws else ''}
    </div>
    """
