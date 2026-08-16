"""
Fact-Checker Agent
Single CodeAgent with tools for summarization and fact-checking
"""

import json
import re
from smolagents import CodeAgent, PythonInterpreterTool, FinalAnswerTool, WikipediaSearchTool
from config import get_model
from tools import analyze_youtube_video, fetch_web_page, better_web_search


def format_result_as_markdown(result) -> str:
    """
    Ensure the agent output is clean, human-friendly Markdown.
    Parses JSON objects/strings if the LLM outputs raw JSON data.
    """
    if result is None:
        return "No result produced by the agent."

    if not isinstance(result, str):
        try:
            result = json.dumps(result, indent=2)
        except Exception:
            result = str(result)

    # Check if result is wrapped in JSON markdown block ```json ... ```
    json_block_match = re.search(r'```(?:json)?\s*(\{[\s\S]*\}|\[[\s\S]*\])\s*```', result)
    if json_block_match:
        json_str = json_block_match.group(1)
    else:
        json_str = result.strip()

    # Try parsing as JSON if it looks like a JSON object or array
    if (json_str.startswith('{') and json_str.endswith('}')) or (json_str.startswith('[') and json_str.endswith(']')):
        try:
            data = json.loads(json_str)
            return _convert_dict_to_markdown(data)
        except Exception:
            pass

    return result


def _convert_dict_to_markdown(data) -> str:
    """Convert dictionary/list data structures to clean Markdown formatting."""
    md_lines = []

    if isinstance(data, dict):
        for key, value in data.items():
            title = key.replace('_', ' ').title()
            md_lines.append(f"## {title}")
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            md_lines.append(f"- **{k.replace('_', ' ').title()}:** {v}")
                        md_lines.append("")
                    else:
                        md_lines.append(f"- {item}")
                md_lines.append("")
            elif isinstance(value, dict):
                for k, v in value.items():
                    md_lines.append(f"- **{k.replace('_', ' ').title()}:** {v}")
                md_lines.append("")
            else:
                md_lines.append(str(value))
                md_lines.append("")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                for k, v in item.items():
                    md_lines.append(f"- **{k.replace('_', ' ').title()}:** {v}")
                md_lines.append("")
            else:
                md_lines.append(f"- {item}")

    return '\n'.join(md_lines)


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
        WikipediaSearchTool(),     # Wikipedia search for reliable reference information
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
        str: Agent's response formatted as Markdown
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

    # Format result to ensure clean Markdown presentation
    return format_result_as_markdown(result)
