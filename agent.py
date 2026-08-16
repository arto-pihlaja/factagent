"""
Fact-Checker Agent
Three discrete phases: fetch, summarize, fact-check
"""

from smolagents import CodeAgent, PythonInterpreterTool, FinalAnswerTool, WikipediaSearchTool
from config import get_model
from tools import analyze_youtube_video, fetch_web_page, better_web_search, _extract_video_id, _get_video_transcript
import re


def is_youtube_url(url: str) -> bool:
    return bool(re.search(r'(youtube\.com|youtu\.be)', url))


def fetch_content(url: str) -> tuple[str, str]:
    """
    Phase 1: Fetch raw content from URL.

    Returns:
        tuple: (source_text, metadata_summary)
            source_text: full raw text for download
            metadata_summary: short description (title, source type, length)
    """
    url = url.strip()
    if is_youtube_url(url):
        video_id = _extract_video_id(url)
        source_text = _get_video_transcript(video_id, include_timestamps=True)
        word_count = len(source_text.split())
        metadata = f"**YouTube video** | ~{word_count:,} words of transcript"
    else:
        source_text = fetch_web_page(url)
        word_count = len(source_text.split())
        metadata = f"**Web page** | ~{word_count:,} words extracted"

    return source_text, metadata


def summarize_content(url: str, source_text: str) -> str:
    """
    Phase 2: Summarize the already-fetched content.

    Args:
        url: original URL (for context)
        source_text: already-fetched text

    Returns:
        str: Markdown summary
    """
    agent = _create_agent()

    prompt = f"""Summarize this content. The text has already been retrieved — do NOT use any fetch tools.

Source URL: {url}

Content:
{source_text[:12000]}

Create a concise summary covering:
- Main topic/thesis
- Key arguments or information
- Important conclusions or takeaways

Format your response as:
## Summary
[3-5 bullet points of key information]
"""
    return agent.run(prompt)


def fact_check_content(url: str, source_text: str) -> str:
    """
    Phase 3: Fact-check claims in the already-fetched content.

    Args:
        url: original URL (for context)
        source_text: already-fetched text

    Returns:
        str: Markdown fact-check results
    """
    agent = _create_agent()

    prompt = f"""Fact-check the key claims in this content. The text has already been retrieved — do NOT use any fetch tools.

Source URL: {url}

Content:
{source_text[:12000]}

Tasks:
1. Identify 3-5 specific verifiable factual claims from the content
2. For each claim, use better_web_search and/or WikipediaSearchTool to find evidence
3. Determine verdict: Supported, Contradicted, Mixed, or Unverified

Format your response as:
## Fact-Check Results

For each claim:
### Claim: [The factual statement]
**Verdict:** [Supported/Contradicted/Mixed/Unverified]
**Evidence:** [Brief summary of what you found]
**Sources:** [URLs or source names]
"""
    return agent.run(prompt)


def _create_agent() -> CodeAgent:
    model = get_model()
    tools = [
        PythonInterpreterTool(),
        analyze_youtube_video,
        fetch_web_page,
        better_web_search,
        WikipediaSearchTool(),
        FinalAnswerTool(),
    ]
    return CodeAgent(
        tools=tools,
        model=model,
        max_steps=15,
        additional_authorized_imports=["json", "re"],
        verbosity_level=1
    )


def run_fact_checker(url: str, enable_fact_check: bool = False):
    """Legacy single-call entry point (kept for compatibility)."""
    source_text, _ = fetch_content(url)
    result = summarize_content(url, source_text)
    if enable_fact_check:
        fc_result = fact_check_content(url, source_text)
        result = result + "\n\n" + fc_result
    return result
