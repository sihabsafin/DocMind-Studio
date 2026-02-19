# DocMind Studio

A multi-agent pipeline that converts YouTube videos into publication-ready blog posts. Paste a URL, configure tone and length, and five specialized LLM agents handle the rest — research, structure, SEO, writing, and editorial review — each passing context to the next.

Built on Streamlit and Groq's inference API. No subscriptions. No OpenAI dependency. Just a Groq API key.

---

## How it works

The core idea is sequential agent specialization. Instead of prompting a single model to "write a blog post about this video," the pipeline breaks the task into five distinct roles, each with a focused system prompt and a specific deliverable. Every agent receives the outputs of all previous agents as context before it runs.

```
YouTube URL
    │
    ▼
Transcript Extraction   (youtube-transcript-api, v0.x + v1.x compatible)
    │
    ▼
[1] Research Analyst    → topics, arguments, evidence, structure suggestions
    │
    ▼
[2] Content Strategist  → H2/H3 outline, hook, transitions, CTA placement
    │
    ▼
[3] SEO Optimizer       → title (60 chars), meta (155 chars), keyword strategy
    │
    ▼
[4] Blog Writer         → full draft in specified tone, ~target word count
    │
    ▼
[5] Quality Reviewer    → grammar, redundancy, tone consistency, final polish
    │
    ▼
Export (Markdown / TXT / HTML)
```

Each agent is a direct call to `llama-3.3-70b-versatile` via the Groq SDK. No framework wrappers, no hidden OpenAI calls. The token budget scales with your length selection — 1,500 tokens for Short up to 6,000 for Epic.

---

## Stack

| Layer | Choice | Why |
|---|---|---|
| UI | Streamlit | Fast iteration, stateful session management |
| Inference | Groq SDK (`groq>=0.4.0`) | Sub-second token generation on Llama 3.3 70B |
| Model | `llama-3.3-70b-versatile` | Strong instruction-following, solid prose quality |
| Transcripts | `youtube-transcript-api` | Handles both v0.x and v1.x API shapes |
| Rendering | `markdown` + custom CSS | Newsreader serif output, editorial feel |

No LangChain. No CrewAI. No vector databases. No embeddings. The pipeline is six files.

---

## Project structure

```
docmind_studio/
├── app.py              Main Streamlit application — all UI stages and routing
├── agents.py           Five-agent pipeline — Groq calls, prompts, context passing
├── utils.py            URL validation, transcript extraction, text utilities
├── styles.py           Complete CSS design system — variables, animations, components
├── requirements.txt    Five dependencies
└── .streamlit/
    └── config.toml     Theme and server config
```

---

## Setup

**Prerequisites:** Python 3.9+, a free Groq API key from [console.groq.com](https://console.groq.com)

```bash
git clone <your-repo>
cd docmind_studio
pip install -r requirements.txt
```

Create `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "gsk_your_key_here"
```

Run:

```bash
streamlit run app.py
```

---

## Deployment on Streamlit Cloud

1. Push to a public GitHub repository
2. Connect at [share.streamlit.io](https://share.streamlit.io)
3. Set `GROQ_API_KEY` in the Secrets dashboard (Settings → Secrets)
4. Deploy

The app reads the key from `st.secrets` first, then falls back to environment variables. Nothing is exposed in the UI.

---

## Configuration

**Writing tones**

| Tone | Behavior |
|---|---|
| Professional | Formal, authoritative, data-referenced |
| Casual | Conversational, contractions, approachable |
| Educational | Structured, step-by-step, clarity-first |
| Storytelling | Narrative-driven, analogy-heavy, emotional arc |
| Technical | Precise, jargon-appropriate, specification-level depth |

**Length targets and token allocation**

| Label | Target words | Max tokens to model |
|---|---|---|
| Short | 800 | 1,500 |
| Medium | 1,500 | 2,500 |
| Long | 2,500 | 4,000 |
| Epic | 4,000 | 6,000 |

**SEO modes**

Basic: title, meta description, primary keyword.

Advanced: adds secondary keywords (5–8), H2/H3 heading optimization suggestions, keyword density recommendation, link-building opportunities, schema markup type.

---

## Groq free tier limits

The free tier as of this writing: 6,000 tokens/minute, 14,400 tokens/day, 30 requests/minute.

Medium-length generations (~1,500 words) consume roughly 3,000–4,000 tokens across five calls. Two or three generations will approach the daily cap. For heavier usage, upgrade to a paid Groq tier — the code does not need to change.

If you hit a 429, the error handler surfaces a readable message rather than a stack trace.

---

## Transcript compatibility

The `youtube-transcript-api` library changed its entire public API in v1.0. The extraction code probes which version is installed at runtime and routes accordingly:

- v0.x: `YouTubeTranscriptApi.get_transcript(video_id)` — class method
- v1.x+: `YouTubeTranscriptApi().fetch(video_id)` — instance method

Three fallback strategies run in sequence: English-preferred fetch, no-language-filter fetch, then listing all available transcripts and picking the best one (manual over auto-generated). If all three fail, the error message tells you exactly why — captions disabled, private video, IP restriction, or genuine absence of captions.

Videos without captions cannot be processed. Most educational, tech, and interview content on YouTube has auto-generated captions. If you hit the wall, the UI surfaces a list of channels that reliably work.

---

## UI features

**Processing stage**

- Per-agent status cards with live progress indicators
- Thought bubbles showing what each agent is "working on" — drawn from a curated set of realistic-sounding internal monologue snippets per agent role
- Live elapsed timer and estimated time remaining (estimates calibrated by length selection)
- Overall pipeline progress bar

**Output stage**

- Confetti animation on first render (canvas-based, brand colors, self-clearing after ~200 frames)
- Sequential paragraph reveal — each element fades and translates up with a 40ms stagger
- Split view toggle — raw Markdown alongside rendered preview, both independently scrollable
- Floating action bar — Copy and Download buttons fixed to viewport, always accessible while scrolling
- SEO metadata panel showing title, meta description, primary keyword, and secondary keywords
- Export to Markdown, plain text, and self-contained HTML (with inline styles, ready to paste into any CMS)

---

## Known constraints

**Streamlit's execution model.** Every widget interaction triggers a full script re-run. Session state carries everything across runs. The agent pipeline runs synchronously inside the Streamlit thread — there is no background worker. For a production deployment handling concurrent users, this would need to move to an async job queue (Celery, RQ, or similar).

**Token context limits.** Each agent receives a truncated slice of previous agents' outputs to stay within the model's context window. The Research Analyst's output is capped at 3,000 tokens when passed to the Content Strategist, and so on down the chain. For very long or dense transcripts, some nuance is lost. Long transcripts are chunked: beginning, middle, and end segments are sampled to fit within 7,000 words before the pipeline starts.

**Groq rate limits on free tier.** Epic-length (4,000 word) generations push the per-minute token limit. If you're running consecutive Epic generations, you will hit a 429. The fix is to wait 60 seconds or switch to a paid tier.

**YouTube IP restrictions.** Some cloud hosting providers have their outbound IPs blocked by YouTube's transcript endpoint. If you see an IP-related error after deploying, try a different provider or route the transcript request through a different egress address.

---

## License

MIT. Do what you want with it.

---

## A note on the architecture decision

The original version of this project used CrewAI to orchestrate the agents. It was removed.

CrewAI >= 0.22 imports OpenAI internally and raises `OPENAI_API_KEY is required` at initialization time, even when you pass a custom LLM instance. The workaround of setting a dummy environment variable worked locally but was fragile and semantically wrong. More importantly, CrewAI added no value here — the orchestration logic is a simple sequential loop with context accumulation, which is fifteen lines of Python. The framework was all overhead and no leverage.

The current implementation calls the Groq API directly. The pipeline is explicit, debuggable, and has no hidden dependencies. If you want to add a new agent, you add a name to a list and write a prompt. That is how it should be.
