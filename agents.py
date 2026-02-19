"""
DocMind Studio — AI Agents Module
5 specialized agents using CrewAI + Groq
"""

from crewai import Agent, Task, Crew, Process
from langchain_groq import ChatGroq
import time


def get_llm(api_key: str, temperature: float = 0.6, max_tokens: int = 2000):
    """Initialize Groq LLM"""
    return ChatGroq(
        api_key=api_key,
        model_name="llama-3.3-70b-versatile",
        temperature=temperature,
        max_tokens=max_tokens,
    )


def create_agents(llm):
    """Create all 5 DocMind agents"""

    research_analyst = Agent(
        role="Content Research Analyst",
        goal="Extract and analyze core concepts, key arguments, and structure from video transcript",
        backstory="""You are an expert content analyst specializing in breaking down video content. 
        You identify main topics, key concepts, supporting evidence, and suggest logical blog structure. 
        You're thorough, analytical, and skilled at spotting the most valuable insights.""",
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    content_strategist = Agent(
        role="Blog Structure Architect",
        goal="Create a compelling, logical blog outline with perfect flow from research findings",
        backstory="""You are a seasoned content strategist who transforms raw research into beautiful 
        blog structures. You know exactly how to hook readers, organize information for maximum impact, 
        and create outlines that writers can turn into excellent long-form content.""",
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    seo_optimizer = Agent(
        role="SEO Optimization Specialist",
        goal="Generate SEO-optimized title, meta description, and keyword strategy to maximize discoverability",
        backstory="""You are an SEO expert who has helped hundreds of blogs achieve top Google rankings. 
        You understand search intent, keyword optimization, and how to craft titles that both rank well 
        and compel clicks. You know the exact character limits and best practices.""",
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    blog_writer = Agent(
        role="Professional Blog Content Writer",
        goal="Write an engaging, human-quality, full blog post based on the outline and SEO strategy",
        backstory="""You are a professional content writer with years of experience creating blog posts 
        that rank, engage, and convert. You adapt your tone perfectly to different styles, write with 
        clarity and depth, and always include strong calls to action. Your writing feels human, not AI.""",
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    quality_reviewer = Agent(
        role="Editorial Quality Reviewer",
        goal="Polish the blog post to publication standards — fix errors, improve clarity, ensure consistency",
        backstory="""You are a seasoned editor with an eye for detail and a commitment to quality. 
        You catch grammatical errors, eliminate redundancy, improve sentence variety, and ensure the 
        final piece is publication-ready. You respect the writer's voice while elevating the content.""",
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    return {
        "research_analyst": research_analyst,
        "content_strategist": content_strategist,
        "seo_optimizer": seo_optimizer,
        "blog_writer": blog_writer,
        "quality_reviewer": quality_reviewer,
    }


def create_tasks(agents, transcript: str, tone: str, word_count: int, seo_mode: str):
    """Create tasks for each agent"""

    tone_instructions = {
        "Professional": "Write in a formal, authoritative, data-driven tone. Use professional vocabulary and cite logical evidence.",
        "Casual": "Write in a conversational, friendly, and relatable tone. Use simple language, contractions, and a warm approach.",
        "Educational": "Write in a clear, structured, tutorial-style tone. Break concepts down step by step for easy understanding.",
        "Storytelling": "Write in a narrative-driven, engaging, and emotional tone. Use stories, analogies, and vivid examples.",
        "Technical": "Write with precision, technical detail, and appropriate jargon. Include specifications and technical depth.",
    }

    tone_desc = tone_instructions.get(tone, tone_instructions["Professional"])

    research_task = Task(
        description=f"""Analyze this YouTube video transcript and extract:
        1. Main topics (3-5 primary themes)
        2. Key concepts and arguments with supporting evidence
        3. Important points worth highlighting in a blog post
        4. Suggested blog sections based on content flow
        5. Any data points, statistics, or examples mentioned
        
        Transcript:
        {transcript[:8000]}
        
        Provide a structured analysis that will help create an excellent blog post.""",
        agent=agents["research_analyst"],
        expected_output="Structured analysis with main topics, key concepts, arguments, and suggested sections",
    )

    strategy_task = Task(
        description=f"""Based on the research analysis, create a compelling blog outline for approximately {word_count} words.
        
        Requirements:
        - Engaging hook in introduction
        - Logical H2/H3 section hierarchy
        - Clear transitions between sections
        - Key takeaways section
        - Strong conclusion
        - Call to action at the end
        - Aim for {word_count} words total
        
        Return a complete markdown outline with ## and ### headings.""",
        agent=agents["content_strategist"],
        expected_output="Complete blog outline in markdown with H2/H3 structure, introduction hook, and conclusion",
        context=[research_task],
    )

    seo_task_desc = f"""Create SEO optimization for this blog post:
        
        Required outputs:
        1. SEO Title (60 characters max, compelling, keyword-rich)
        2. Meta Description (155 characters max, includes primary keyword, has CTA)
        3. Primary Keyword (single most important keyword)
        """

    if seo_mode == "Advanced":
        seo_task_desc += """
        4. Secondary Keywords (5-8 related keywords)
        5. Optimized H2/H3 heading suggestions
        6. Keyword density recommendations
        7. Link building opportunities (types of sites to link to)
        8. Schema markup type recommendation
        """

    seo_task_desc += "\n\nFormat your response clearly with labeled sections."

    seo_task = Task(
        description=seo_task_desc,
        agent=agents["seo_optimizer"],
        expected_output="SEO title, meta description, primary keyword, and additional SEO metadata",
        context=[research_task, strategy_task],
    )

    write_task = Task(
        description=f"""Write a complete, publication-ready blog post following these specifications:
        
        Tone: {tone_desc}
        Target Length: approximately {word_count} words
        
        Requirements:
        - Follow the outline structure exactly
        - Use the SEO title and integrate keywords naturally
        - Write with the specified tone throughout
        - Include relevant examples and actionable insights
        - Use bullet points and numbered lists for scannability
        - Add a strong call-to-action at the end
        - Make it feel human-written, not AI-generated
        
        Format the entire blog post in proper Markdown with:
        - # for main title
        - ## for H2 sections
        - ### for H3 subsections
        - **bold** for emphasis
        - Bullet lists and numbered lists where appropriate
        
        Include at the very top:
        **SEO Title:** [the SEO-optimized title]
        **Meta Description:** [the meta description]
        **Primary Keyword:** [primary keyword]
        
        Then the full blog post content below.""",
        agent=agents["blog_writer"],
        expected_output="Complete blog post in Markdown format with SEO metadata at top and full content",
        context=[research_task, strategy_task, seo_task],
    )

    review_task = Task(
        description="""Review and polish the blog post to publication standards:
        
        1. Fix any grammatical errors or typos
        2. Eliminate repetitive phrases or redundant content
        3. Improve sentence variety and readability
        4. Ensure tone is consistent throughout
        5. Verify the call-to-action is strong and clear
        6. Ensure headings are compelling and descriptive
        7. Check that the content flows naturally
        
        Return the COMPLETE polished blog post in Markdown format.
        Keep the SEO Title, Meta Description, and Primary Keyword at the top.
        Do not remove or summarize content — return the full, improved post.""",
        agent=agents["quality_reviewer"],
        expected_output="Final polished blog post in Markdown format, publication-ready",
        context=[write_task],
    )

    return [research_task, strategy_task, seo_task, write_task, review_task]


def run_agent_pipeline(
    api_key: str,
    transcript: str,
    tone: str,
    word_count: int,
    seo_mode: str,
    progress_callbacks: dict = None,
) -> dict:
    """
    Run the full multi-agent pipeline.
    Returns dict with final blog content and metadata.
    """

    max_tokens_map = {
        800: 1500,
        1500: 2500,
        2500: 4000,
        4000: 6000,
    }
    max_tokens = max_tokens_map.get(word_count, 2500)

    llm = get_llm(api_key, temperature=0.6, max_tokens=max_tokens)
    agents = create_agents(llm)

    agent_order = [
        ("research_analyst", "Research Analyst"),
        ("content_strategist", "Content Strategist"),
        ("seo_optimizer", "SEO Optimizer"),
        ("blog_writer", "Blog Writer"),
        ("quality_reviewer", "Quality Reviewer"),
    ]

    results = {}

    for i, (agent_key, agent_name) in enumerate(agent_order):
        if progress_callbacks and "on_agent_start" in progress_callbacks:
            progress_callbacks["on_agent_start"](i, agent_name)

        start_time = time.time()

        # Create and run individual task
        task_list = create_tasks(agents, transcript, tone, word_count, seo_mode)
        task = task_list[i]

        # For sequential tasks, we need context from previous results
        if i == 0:
            mini_crew = Crew(
                agents=[agents[agent_key]],
                tasks=[task],
                process=Process.sequential,
                verbose=False,
            )
        else:
            # Pass previous results as context in the task description
            context_summary = "\n\n".join(
                [f"Previous agent output:\n{v}" for v in results.values()]
            )
            task.description = task.description + f"\n\nContext from previous agents:\n{context_summary[:3000]}"
            mini_crew = Crew(
                agents=[agents[agent_key]],
                tasks=[task],
                process=Process.sequential,
                verbose=False,
            )

        result = mini_crew.kickoff()
        duration = round(time.time() - start_time, 1)
        results[agent_key] = str(result)

        if progress_callbacks and "on_agent_complete" in progress_callbacks:
            progress_callbacks["on_agent_complete"](i, agent_name, duration)

    final_blog = results.get("quality_reviewer", results.get("blog_writer", ""))

    return {
        "blog_content": final_blog,
        "research": results.get("research_analyst", ""),
        "outline": results.get("content_strategist", ""),
        "seo": results.get("seo_optimizer", ""),
        "word_count": len(final_blog.split()),
    }
