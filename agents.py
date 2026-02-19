"""
DocMind Studio — AI Agents Pipeline
5 specialized agents using Groq API directly (no CrewAI OpenAI dependency)

Why direct Groq instead of CrewAI?
CrewAI >=0.22 internally imports OpenAI and requires OPENAI_API_KEY even when
you pass a custom LLM. To avoid this, we call the Groq API directly via the
groq Python SDK — same multi-agent logic, zero OpenAI dependency.
"""

import os
import time
from groq import Groq


# ── Dummy env var to silence any CrewAI/LangChain OpenAI checks ─────────────
os.environ.setdefault("OPENAI_API_KEY", "sk-dummy-not-used-docmind")


def _call_groq(
    client: Groq,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 2500,
    temperature: float = 0.65,
) -> str:
    """Single Groq API call — returns response text."""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


# ── Agent system prompts ──────────────────────────────────────────────────────

AGENT_SYSTEMS = {
    "Research Analyst": """You are an expert content analyst specializing in breaking down video transcripts.
Your job is to extract the most valuable insights, identify key themes, core arguments, 
supporting evidence, and suggest a logical structure for a blog post.
Be thorough, analytical, and focus on what would matter most to readers.
Return a clear, structured analysis.""",

    "Content Strategist": """You are a seasoned content strategist who transforms research into compelling blog structures.
You know how to hook readers, organize information for maximum impact, and design outlines
that guide writers to produce excellent long-form content.
Return a complete, well-structured markdown blog outline with H2 and H3 headings.""",

    "SEO Optimizer": """You are an SEO expert with a track record of helping blogs rank on Google's first page.
You understand search intent, keyword optimization, and how to craft titles that rank AND get clicks.
You know exact character limits and best practices.
Return clearly labeled SEO metadata.""",

    "Blog Writer": """You are a professional blog writer who creates engaging, human-quality content.
You adapt your tone perfectly, write with clarity and depth, and always include strong calls to action.
Your writing feels genuinely human — not like AI-generated filler.
Return a complete, well-formatted blog post in Markdown.""",

    "Quality Reviewer": """You are a seasoned editor committed to publication-quality content.
You catch grammatical errors, eliminate redundancy, improve sentence variety, 
ensure consistent tone, and make every word count.
Return the COMPLETE polished blog post — do not summarize or shorten it.""",
}

TONE_INSTRUCTIONS = {
    "Professional":  "Use a formal, authoritative, data-driven tone. Professional vocabulary, logical evidence.",
    "Casual":        "Use a conversational, friendly, relatable tone. Simple language, contractions, warm approach.",
    "Educational":   "Use a clear, structured, tutorial-style tone. Break concepts down step by step.",
    "Storytelling":  "Use a narrative-driven, engaging, emotional tone. Stories, analogies, vivid examples.",
    "Technical":     "Use precise, technical, jargon-appropriate language. Include specifications and depth.",
}


def run_agent_pipeline(
    api_key: str,
    transcript: str,
    tone: str,
    word_count: int,
    seo_mode: str,
    progress_callbacks: dict = None,
) -> dict:
    """
    Run the full 5-agent pipeline using Groq directly.
    Returns dict with blog_content and metadata.
    """
    client = Groq(api_key=api_key)

    max_tokens_map = {800: 1500, 1500: 2500, 2500: 4000, 4000: 6000}
    max_tokens = max_tokens_map.get(word_count, 2500)
    tone_desc = TONE_INSTRUCTIONS.get(tone, TONE_INSTRUCTIONS["Professional"])

    agent_order = [
        "Research Analyst",
        "Content Strategist",
        "SEO Optimizer",
        "Blog Writer",
        "Quality Reviewer",
    ]

    results = {}

    for i, agent_name in enumerate(agent_order):

        # ── Notify UI: agent starting ──────────────────────────────────────
        if progress_callbacks and "on_agent_start" in progress_callbacks:
            progress_callbacks["on_agent_start"](i, agent_name)

        start_time = time.time()
        context = "\n\n".join(
            f"=== {k} Output ===\n{v}" for k, v in results.items()
        )

        # ── Build task prompt for each agent ──────────────────────────────
        if agent_name == "Research Analyst":
            user_prompt = f"""Analyze this YouTube video transcript and extract:
1. Main topics (3–5 primary themes)
2. Key concepts and arguments with supporting evidence
3. Important points worth highlighting in a blog post
4. Suggested blog sections based on content flow
5. Any data points, statistics, or examples mentioned

Transcript:
{transcript[:7000]}

Provide a structured analysis to help create an excellent blog post."""

        elif agent_name == "Content Strategist":
            user_prompt = f"""Based on this research analysis, create a compelling blog outline for ~{word_count} words.

Research:
{results.get('Research Analyst', '')[:3000]}

Requirements:
- Engaging hook in the introduction
- Logical H2/H3 section hierarchy
- Clear transitions between sections
- Key takeaways section
- Strong conclusion
- Call to action

Return a complete markdown outline with ## and ### headings."""

        elif agent_name == "SEO Optimizer":
            seo_extras = ""
            if seo_mode == "Advanced":
                seo_extras = """
4. Secondary Keywords (5–8 related keywords, comma-separated)
5. Optimized H2/H3 heading suggestions
6. Keyword density recommendation (%)
7. Link building opportunities
8. Schema markup type"""

            user_prompt = f"""Create SEO optimization based on this content:

Research Summary:
{results.get('Research Analyst', '')[:2000]}

Blog Outline:
{results.get('Content Strategist', '')[:1500]}

Required outputs:
1. SEO Title (60 chars max, compelling, keyword-rich)
2. Meta Description (155 chars max, includes primary keyword + CTA)
3. Primary Keyword (single most important keyword){seo_extras}

Format with clear labels like:
SEO Title: ...
Meta Description: ...
Primary Keyword: ..."""

        elif agent_name == "Blog Writer":
            user_prompt = f"""Write a complete, publication-ready blog post.

Tone: {tone_desc}
Target Length: approximately {word_count} words

Blog Outline:
{results.get('Content Strategist', '')[:2000]}

SEO Guidelines:
{results.get('SEO Optimizer', '')[:1000]}

Requirements:
- Follow the outline structure
- Integrate keywords naturally (don't keyword-stuff)
- Write with the specified tone throughout
- Include relevant examples and actionable insights
- Use bullet points and numbered lists for scannability
- End with a strong call-to-action
- Write naturally — avoid sounding like AI

Format in Markdown (# H1, ## H2, ### H3, **bold**, bullet lists).

Start with these metadata lines at the very top:
**SEO Title:** [title here]
**Meta Description:** [meta here]
**Primary Keyword:** [keyword here]

Then write the full blog post below."""

        elif agent_name == "Quality Reviewer":
            user_prompt = f"""Review and polish this blog post to publication standards:

{results.get('Blog Writer', '')}

Tasks:
1. Fix grammatical errors and typos
2. Eliminate repetitive phrases and redundant content
3. Improve sentence variety and readability
4. Ensure tone is consistent throughout
5. Strengthen the call-to-action if weak
6. Make headings more compelling if needed
7. Ensure natural content flow

IMPORTANT: Return the COMPLETE polished blog post in Markdown.
Keep SEO Title, Meta Description, and Primary Keyword at the top.
Do NOT shorten, summarize, or remove content."""

        else:
            user_prompt = f"Process the following:\n\n{context}"

        # ── Call Groq ──────────────────────────────────────────────────────
        output = _call_groq(
            client=client,
            system_prompt=AGENT_SYSTEMS[agent_name],
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=0.65,
        )
        results[agent_name] = output

        duration = round(time.time() - start_time, 1)

        # ── Notify UI: agent complete ──────────────────────────────────────
        if progress_callbacks and "on_agent_complete" in progress_callbacks:
            progress_callbacks["on_agent_complete"](i, agent_name, duration)

    final_blog = results.get("Quality Reviewer", results.get("Blog Writer", ""))

    return {
        "blog_content": final_blog,
        "research":     results.get("Research Analyst", ""),
        "outline":      results.get("Content Strategist", ""),
        "seo":          results.get("SEO Optimizer", ""),
        "word_count":   len(final_blog.split()),
    }
