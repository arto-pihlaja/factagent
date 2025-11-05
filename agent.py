"""
Fact-Checker Agent
Single CodeAgent with tools for summarization and fact-checking
"""

from smolagents import CodeAgent, PythonInterpreterTool, FinalAnswerTool
from config import get_model
from tools import analyze_youtube_video, fetch_web_page, better_web_search


def create_fact_checker_agent():
    """
    Create and configure the fact-checker agent.

    Returns:
        CodeAgent: Configured agent ready to use
    """
    # Get model from config
    model = get_model()

    # Define tools
    tools = [
        PythonInterpreterTool(),  # For data processing and analysis
        analyze_youtube_video,     # YouTube transcript extraction
        fetch_web_page,            # Web article extraction
        better_web_search,         # Web search for fact-checking
        FinalAnswerTool(),         # Final answer formatting
    ]

    # Create agent
    agent = CodeAgent(
        tools=tools,
        model=model,
        max_steps=15,
        additional_authorized_imports=["json", "re"],
        verbosity_level=1
    )

    return agent


def run_fact_checker(url: str, enable_fact_check: bool = False):
    """
    Run fact-checker agent on a given URL.

    Args:
        url: URL to analyze (YouTube video or web page)
        enable_fact_check: Whether to perform fact-checking (default: False)

    Returns:
        str: Agent's response
    """
    agent = create_fact_checker_agent()

    # Build prompt based on fact-check flag
    if enable_fact_check:
        prompt = f"""Analyze this content and provide both a summary and fact-checking:

URL: {url}

Tasks:
1. Retrieve and read the content from the URL
   - If YouTube: Use analyze_youtube_video tool
   - Otherwise: Use fetch_web_page tool

2. Create a concise summary (3-5 key points)

3. Fact-check the content:
   - Identify 3-5 verifiable factual claims
   - For each claim, search for supporting or contradicting evidence using better_web_search
   - Determine verdict: Supported, Contradicted, Mixed, or Unverified
   - List sources used for verification

Format your response as:
## Summary
[3-5 bullet points of key information]

## Fact-Check Results
[For each claim, provide:]
- Claim: [The factual statement]
- Verdict: [Supported/Contradicted/Mixed/Unverified]
- Evidence: [Brief summary with source links]
"""
    else:
        prompt = f"""Analyze this content and provide a summary:

URL: {url}

Tasks:
1. Retrieve and read the content from the URL
   - If YouTube: Use analyze_youtube_video tool
   - Otherwise: Use fetch_web_page tool

2. Create a concise summary (3-5 key points) covering:
   - Main topic/thesis
   - Key arguments or information
   - Important conclusions or takeaways

Format your response as:
## Summary
[3-5 bullet points of key information]
"""

    # Run agent
    result = agent.run(prompt)

    return result
