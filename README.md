---
title: Fact-Checker
emoji: 🔍
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 5.49.1
app_file: app.py
pinned: false
---

# Fact-Checker Agent

An AI-powered tool that summarizes web content and optionally fact-checks claims using smolagents.

## Features

- **Content Summarization**: Get concise summaries of YouTube videos and web articles
- **YouTube Support**: Automatically extracts and analyzes video transcripts
- **Web Article Support**: Works with Substack, blogs, news sites, and more
- **Fact-Checking**: Optional claim verification with evidence from reliable sources

## How to Use

1. **Enter a URL**: Paste a YouTube video link or web article URL
2. **Optional**: Enable fact-checking to verify key claims
3. **Click Analyze**: Get your summary and (optional) fact-check results

## Supported Sources

- YouTube videos (with available transcripts)
- News articles
- Blog posts (including Substack)
- Wikipedia articles
- Most web pages with readable text content

## Setup (For Local Development)

### Requirements

- Python 3.10+
- OpenRouter API key
- Serper API key (for fact-checking)

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create `.env` file with your API keys:
   ```bash
   OPENROUTER_API_KEY=your_key_here
   SERPER_API_KEY=your_key_here
   ```

4. Run the app:
   ```bash
   python app.py
   ```

## Technology

Built with:
- [smolagents](https://github.com/huggingface/smolagents) - Agentic framework
- [Gradio](https://gradio.app/) - UI framework
- [OpenRouter](https://openrouter.ai/) - LLM provider
- [Serper](https://serper.dev/) - Web search API

## Architecture

Single-agent system using CodeAgent pattern:
- Retrieves content (YouTube transcripts or web pages)
- Summarizes key points
- Optionally extracts and verifies factual claims

## Limitations

- Fact-checking accuracy depends on LLM capabilities and available sources
- Long videos/articles may be truncated
- Requires available transcripts for YouTube videos
- Some websites may block automated access

## License

MIT License

## Acknowledgments

Based on the smolagents framework by Hugging Face.
