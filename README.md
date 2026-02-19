# ◈ DocMind Studio
## YouTube to Blog Automation Platform

> **Transform any YouTube video into a publication-ready, SEO-optimized blog post using 5 specialized AI agents.**

Built with **Streamlit + CrewAI + Groq (Llama 3.3 70B)**

---

## ✨ Features

- 🔬 **5 Specialized AI Agents** — Research → Strategy → SEO → Writing → Quality Review
- 📺 **YouTube Integration** — Supports standard, shorts, and mobile URLs
- 🎨 **5 Writing Tones** — Professional, Casual, Educational, Storytelling, Technical  
- 📏 **4 Length Options** — Short (800w) to Epic (4000w+)
- 🔍 **Basic & Advanced SEO** — Title, meta, keywords, headings, link opportunities
- 📥 **Multiple Export Formats** — Markdown, TXT, HTML
- ⚡ **Real-Time Agent Visibility** — Watch each agent work in real time
- 🆓 **Free to Deploy** — Groq free tier, Streamlit Cloud

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/docmind-studio
cd docmind-studio
pip install -r requirements.txt
```

### 2. Get API Keys

**Groq API Key (Free):**
- Visit [console.groq.com](https://console.groq.com)
- Sign up → Create API Key
- Starts with `gsk_...`

### 3. Configure Secrets

Create `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "gsk_your_key_here"
```

> ⚠️ **Never commit your API key!** The `.gitignore` already excludes `secrets.toml`

### 4. Run

```bash
streamlit run app.py
```

---

## 🏗 Architecture

```
User Input (YouTube URL)
       ↓
URL Validation + Video ID Extraction
       ↓
Transcript Extraction (youtube-transcript-api)
       ↓
Multi-Agent Orchestration (CrewAI Sequential)
       ↓
┌─────────────────────────────────┐
│  Agent 1: Research Analyst      │ → Key concepts, structure, insights
├─────────────────────────────────┤
│  Agent 2: Content Strategist    │ → Blog outline, flow, hierarchy
├─────────────────────────────────┤
│  Agent 3: SEO Optimizer         │ → Title, meta, keywords, headings
├─────────────────────────────────┤
│  Agent 4: Blog Writer           │ → Full content in chosen tone
├─────────────────────────────────┤
│  Agent 5: Quality Reviewer      │ → Polish, accuracy, consistency
└─────────────────────────────────┘
       ↓
Final Blog Output (Markdown + Metadata)
       ↓
Streamlit UI + Export Options
```

---

## 📁 Project Structure

```
docmind_studio/
├── app.py              # Main Streamlit application
├── agents.py           # CrewAI agent definitions and pipeline
├── utils.py            # YouTube utilities, text processing
├── styles.py           # Complete CSS design system
├── requirements.txt    # Python dependencies
├── .streamlit/
│   ├── config.toml     # Streamlit configuration
│   └── secrets.toml    # API keys (do NOT commit)
└── README.md
```

---

## ☁️ Deploy to Streamlit Cloud

1. Push code to GitHub (without `secrets.toml`)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set main file: `app.py`
5. Add secrets in Streamlit Cloud dashboard:
   ```
   GROQ_API_KEY = "gsk_..."
   ```
6. Deploy!

---

## ⚙️ Configuration

### AI Model
- **Primary:** Groq Llama 3.3 70B (free tier)
- **Rate Limits:** 30 requests/min, 14,400 tokens/day
- **Temperature:** 0.6 (balanced creativity)

### Transcript Limits
- **< 5,000 words:** Full processing
- **5,000–15,000 words:** Smart chunking (beginning + middle + end)
- **> 15,000 words:** Key segment extraction

### Token Allocation
| Length | Max Tokens |
|--------|------------|
| Short (800w) | 1,500 |
| Medium (1,500w) | 2,500 |
| Long (2,500w) | 4,000 |
| Epic (4,000w) | 6,000 |

---

## 🛠 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Transcript not available" | Try a video with captions enabled |
| "Invalid API key" | Check your Groq key starts with `gsk_` |
| "Rate limit reached" | Wait 60 seconds (free tier limit) |
| "Video too long" | Try videos under 30 minutes |
| Agent pipeline fails | Check Groq API status, retry once |

---

## 🔮 Roadmap (Phase 2)

- [ ] Multi-video synthesis
- [ ] LinkedIn/Twitter thread generator
- [ ] AI cover image generation
- [ ] WordPress/Medium direct publish
- [ ] Newsletter format output
- [ ] NVIDIA API comparison mode

---

## 📄 License

MIT License — Free for personal and commercial use.

---

*DocMind Studio v2.0 | Multi-Agent Content Automation*
