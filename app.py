"""
Gradio UI for Fact-Checker Agent
Step-by-step flow: Fetch → Summary → Fact-check
Each phase appends to the results and asks user to continue.
"""

import os
import tempfile
from datetime import datetime
import gradio as gr
from agent import fetch_content, summarize_content, fact_check_content, is_youtube_url


# ---------------------------------------------------------------------------
# Phase handlers
# ---------------------------------------------------------------------------

def phase_fetch(url: str, state: dict):
    """
    Phase 1: Fetch raw content.
    Returns updated state and UI updates.
    """
    if not url or not url.strip():
        yield (
            state,
            gr.update(),        # content_display
            gr.update(),        # source_file
            gr.update(),        # results_md
            gr.update(visible=False),  # summarize_btn
            gr.update(visible=False),  # factcheck_btn
            gr.update(visible=False),  # fetch_status
            "Please enter a URL.",     # status_msg
        )
        return

    url = url.strip()

    yield (
        state,
        gr.update(value="*Fetching content...*", visible=True),
        gr.update(visible=False),
        gr.update(),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        "Fetching content from source...",
    )

    try:
        source_text, metadata = fetch_content(url)
    except Exception as e:
        yield (
            state,
            gr.update(value=f"**Error fetching content:** {e}", visible=True),
            gr.update(visible=False),
            gr.update(value=""),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            f"Error: {e}",
        )
        return

    # Save source text to temp file for download
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir = tempfile.gettempdir()
    ext = "txt"
    fname = f"source_{timestamp}.{ext}"
    fpath = os.path.join(temp_dir, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(source_text)

    # Update state
    new_state = dict(state)
    new_state["url"] = url
    new_state["source_text"] = source_text
    new_state["results"] = ""

    preview = source_text[:2000] + ("\n\n*[truncated — download for full text]*" if len(source_text) > 2000 else "")

    content_md = f"### Fetched Content\n\n{metadata}\n\n<details>\n<summary>Preview source text</summary>\n\n```\n{preview}\n```\n</details>"

    yield (
        new_state,
        gr.update(value=content_md, visible=True),
        gr.update(value=fpath, visible=True),
        gr.update(value=""),
        gr.update(visible=True, value="Summarize →"),
        gr.update(visible=False),
        gr.update(visible=False),
        "Content fetched. Click **Summarize** to continue.",
    )


def phase_summarize(state: dict):
    """Phase 2: Summarize content."""
    url = state.get("url", "")
    source_text = state.get("source_text", "")

    if not source_text:
        yield (
            state,
            gr.update(),
            gr.update(),
            gr.update(visible=False),
            gr.update(visible=False),
            "No content to summarize. Please fetch a URL first.",
        )
        return

    yield (
        state,
        gr.update(value="*Summarizing content — this may take a moment...*"),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        "Summarizing...",
    )

    try:
        summary = summarize_content(url, source_text)
    except Exception as e:
        yield (
            state,
            gr.update(value=f"**Error during summarization:** {e}"),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            f"Error: {e}",
        )
        return

    new_state = dict(state)
    new_state["results"] = summary
    new_state["summary"] = summary

    # Save analysis file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir = tempfile.gettempdir()
    fpath = os.path.join(temp_dir, f"analysis_{timestamp}.md")
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(f"# Fact-Checker Analysis\n\n**Source:** {url}\n\n{summary}")

    next_step_note = "\n\n---\n*Next step: **Fact-check** — verify key claims against external sources (takes longer).*"

    yield (
        new_state,
        gr.update(value=summary + next_step_note),
        gr.update(value=fpath, visible=True),
        gr.update(visible=True, value="Fact-check →"),
        gr.update(visible=True, value="Summarize →"),
        "Summary ready. Click **Fact-check** to verify claims, or you're done.",
    )


def phase_factcheck(state: dict):
    """Phase 3: Fact-check claims."""
    url = state.get("url", "")
    source_text = state.get("source_text", "")
    summary = state.get("summary", "")

    if not source_text:
        yield (
            state,
            gr.update(),
            gr.update(),
            gr.update(visible=False),
            gr.update(visible=True),
            "No content to fact-check. Please fetch a URL first.",
        )
        return

    yield (
        state,
        gr.update(value=(summary or "") + "\n\n---\n*Fact-checking claims — searching for evidence...*"),
        gr.update(),
        gr.update(visible=False),
        gr.update(visible=False),
        "Fact-checking in progress...",
    )

    try:
        fc_result = fact_check_content(url, source_text)
    except Exception as e:
        yield (
            state,
            gr.update(value=(summary or "") + f"\n\n**Error during fact-check:** {e}"),
            gr.update(),
            gr.update(visible=False),
            gr.update(visible=True),
            f"Error: {e}",
        )
        return

    new_state = dict(state)
    combined = (summary or "") + "\n\n---\n\n" + fc_result
    new_state["results"] = combined

    # Update analysis file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir = tempfile.gettempdir()
    fpath = os.path.join(temp_dir, f"analysis_{timestamp}.md")
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(f"# Fact-Checker Analysis\n\n**Source:** {url}\n\n{combined}")

    yield (
        new_state,
        gr.update(value=combined),
        gr.update(value=fpath, visible=True),
        gr.update(visible=False),
        gr.update(visible=True),
        "Fact-check complete.",
    )


# ---------------------------------------------------------------------------
# Build UI
# ---------------------------------------------------------------------------

with gr.Blocks(title="Fact-Checker", css=".status-bar { font-style: italic; color: #666; }") as demo:
    gr.Markdown("# Fact-Checker Agent\nSummarize web content and fact-check claims — step by step.")

    state = gr.State({})

    with gr.Row():
        # Left column: inputs
        with gr.Column(scale=1):
            url_input = gr.Textbox(
                label="URL",
                placeholder="YouTube URL or web article URL...",
                lines=2
            )
            fetch_btn = gr.Button("Fetch content", variant="primary")
            status_msg = gr.Markdown("*Enter a URL and click Fetch content to begin.*")

        # Right column: results
        with gr.Column(scale=2):
            # Phase 1 output: fetched content preview + source download
            content_display = gr.Markdown(visible=False)
            source_file = gr.File(label="Download source text", visible=False)

            # Phase 2/3 output: summary + fact-check
            results_md = gr.Markdown()
            analysis_file = gr.File(label="Download analysis (.md)", visible=False)

            with gr.Row():
                summarize_btn = gr.Button("Summarize →", variant="primary", visible=False)
                factcheck_btn = gr.Button("Fact-check →", variant="secondary", visible=False)

    gr.Markdown("### Examples")
    gr.Examples(
        examples=[
            ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
            ["https://en.wikipedia.org/wiki/Artificial_intelligence"],
        ],
        inputs=[url_input],
        label="Try these"
    )

    # ---------------------------------------------------------------------------
    # Event wiring
    # ---------------------------------------------------------------------------

    fetch_outputs = [
        state,
        content_display,
        source_file,
        results_md,
        summarize_btn,
        factcheck_btn,
        analysis_file,
        status_msg,
    ]

    fetch_btn.click(
        fn=phase_fetch,
        inputs=[url_input, state],
        outputs=fetch_outputs,
    )
    url_input.submit(
        fn=phase_fetch,
        inputs=[url_input, state],
        outputs=fetch_outputs,
    )

    summarize_outputs = [
        state,
        results_md,
        analysis_file,
        factcheck_btn,
        summarize_btn,
        status_msg,
    ]

    summarize_btn.click(
        fn=phase_summarize,
        inputs=[state],
        outputs=summarize_outputs,
    )

    factcheck_outputs = [
        state,
        results_md,
        analysis_file,
        factcheck_btn,
        summarize_btn,
        status_msg,
    ]

    factcheck_btn.click(
        fn=phase_factcheck,
        inputs=[state],
        outputs=factcheck_outputs,
    )


if __name__ == "__main__":
    demo.launch()
