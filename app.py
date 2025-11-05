"""
Gradio UI for Fact-Checker Agent
Simple interface for summarizing and fact-checking web content
"""

import gradio as gr
from agent import run_fact_checker


def process_url(url: str, enable_fact_check: bool):
    """
    Process URL through fact-checker agent.

    Args:
        url: URL to analyze
        enable_fact_check: Whether to enable fact-checking

    Returns:
        str: Analysis result
    """
    if not url or not url.strip():
        return "Please enter a URL to analyze."

    try:
        result = run_fact_checker(url.strip(), enable_fact_check)
        return result
    except Exception as e:
        return f"Error processing URL: {str(e)}\n\nPlease check that:\n1. The URL is valid\n2. Environment variables are set (OPENROUTER_API_KEY, SERPER_API_KEY)"


# Create Gradio interface
with gr.Blocks(title="Fact-Checker") as demo:
    gr.Markdown("""
    # Fact-Checker Agent

    Summarize web content and optionally fact-check claims.

    **Supported sources:**
    - YouTube videos (extracts transcripts)
    - Web articles (Substack, blogs, news sites)
    - Any web page with readable content
    """)

    with gr.Row():
        with gr.Column():
            url_input = gr.Textbox(
                label="URL",
                placeholder="Enter YouTube URL or web article URL...",
                lines=2
            )

            fact_check_checkbox = gr.Checkbox(
                label="Enable fact-checking",
                value=False,
                info="Extract and verify key claims (takes longer)"
            )

            submit_btn = gr.Button("Analyze", variant="primary")

        with gr.Column():
            output = gr.Textbox(
                label="Analysis Result",
                lines=20,
                show_copy_button=True
            )

    # Examples
    gr.Markdown("### Examples")
    gr.Examples(
        examples=[
            ["https://www.youtube.com/watch?v=dQw4w9WgXcQ", False],
            ["https://en.wikipedia.org/wiki/Artificial_intelligence", False],
            ["https://en.wikipedia.org/wiki/Artificial_intelligence", True],
        ],
        inputs=[url_input, fact_check_checkbox],
        label="Try these examples"
    )

    # Event handler
    submit_btn.click(
        fn=process_url,
        inputs=[url_input, fact_check_checkbox],
        outputs=output
    )

    # Also trigger on Enter key
    url_input.submit(
        fn=process_url,
        inputs=[url_input, fact_check_checkbox],
        outputs=output
    )

if __name__ == "__main__":
    demo.launch()
