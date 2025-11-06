"""
Gradio UI for Fact-Checker Agent
Simple interface for summarizing and fact-checking web content
"""

import os
import re
import tempfile
from datetime import datetime
import gradio as gr
from agent import run_fact_checker
from tools import _extract_video_id, _get_video_transcript, fetch_web_page


def is_youtube_url(url: str) -> bool:
    """Check if URL is a YouTube video."""
    return bool(re.search(r'(youtube\.com|youtu\.be)', url))


def process_url(url: str, enable_fact_check: bool, enable_download: bool, include_timestamps: bool):
    """
    Process URL through fact-checker agent.

    Args:
        url: URL to analyze
        enable_fact_check: Whether to enable fact-checking
        enable_download: Whether to generate downloadable text file
        include_timestamps: Whether to include timestamps (YouTube only)

    Returns:
        tuple: (analysis_result, download_file_path or None)
    """
    if not url or not url.strip():
        return "Please enter a URL to analyze.", None

    try:
        # Run the analysis
        result = run_fact_checker(url.strip(), enable_fact_check)

        # Generate download file if requested
        download_file = None
        if enable_download:
            try:
                is_youtube = is_youtube_url(url.strip())

                if is_youtube:
                    # Extract YouTube transcript
                    video_id = _extract_video_id(url.strip())
                    transcript_text = _get_video_transcript(video_id, include_timestamps=include_timestamps)
                    filename = f"transcript_{video_id}.txt"
                else:
                    # Fetch web page content
                    transcript_text = fetch_web_page(url.strip())
                    # Create filename from timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"webpage_{timestamp}.txt"

                # Save to temporary file
                temp_dir = tempfile.gettempdir()
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(transcript_text)

                download_file = file_path
            except Exception as e:
                # Don't fail the whole process if download fails
                result += f"\n\n[Note: Could not generate download file: {str(e)}]"

        return result, download_file

    except Exception as e:
        return f"Error processing URL: {str(e)}\n\nPlease check that:\n1. The URL is valid\n2. Environment variables are set (OPENROUTER_API_KEY, SERPER_API_KEY)", None


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

            download_checkbox = gr.Checkbox(
                label="Download analyzed text",
                value=False,
                info="Download the full source text as a .txt file"
            )

            timestamp_checkbox = gr.Checkbox(
                label="Include timestamps (YouTube only)",
                value=True,
                visible=False,
                info="Format: [mm:ss], text"
            )

            submit_btn = gr.Button("Analyze", variant="primary")

        with gr.Column():
            output = gr.Textbox(
                label="Analysis Result",
                lines=20,
                show_copy_button=True
            )

            download_file = gr.File(
                label="Download File",
                visible=True
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

    # Dynamic UI: Show timestamp checkbox when download is enabled and URL is YouTube
    def update_timestamp_visibility(url, download_enabled):
        """Show timestamp checkbox only for YouTube URLs when download is enabled."""
        if download_enabled and url and is_youtube_url(url):
            return gr.update(visible=True)
        return gr.update(visible=False)

    # Update timestamp checkbox visibility when URL or download checkbox changes
    url_input.change(
        fn=update_timestamp_visibility,
        inputs=[url_input, download_checkbox],
        outputs=timestamp_checkbox
    )

    download_checkbox.change(
        fn=update_timestamp_visibility,
        inputs=[url_input, download_checkbox],
        outputs=timestamp_checkbox
    )

    # Event handler
    submit_btn.click(
        fn=process_url,
        inputs=[url_input, fact_check_checkbox, download_checkbox, timestamp_checkbox],
        outputs=[output, download_file]
    )

    # Also trigger on Enter key
    url_input.submit(
        fn=process_url,
        inputs=[url_input, fact_check_checkbox, download_checkbox, timestamp_checkbox],
        outputs=[output, download_file]
    )

if __name__ == "__main__":
    demo.launch()
