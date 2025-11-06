"""
Core tools for Fact-Checker Agent
Reused from course_final_ass with minimal modifications for MVP
"""

import os
import re
import json
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
import html2text
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

from smolagents import tool


# ============================================================================
# YOUTUBE VIDEO ANALYSIS
# ============================================================================

def _extract_video_id(url: str) -> str:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\?/]+)',
        r'youtube\.com/watch\?.*v=([^&]+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    raise ValueError(f"Could not extract video ID from URL: {url}")


def _get_video_metadata(video_id: str) -> dict:
    """Fetch video metadata using yt-dlp."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }

    url = f"https://www.youtube.com/watch?v={video_id}"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        return {
            'title': info.get('title', 'Unknown'),
            'description': info.get('description', ''),
            'duration': info.get('duration', 0),
            'upload_date': info.get('upload_date', ''),
            'uploader': info.get('uploader', 'Unknown'),
            'view_count': info.get('view_count', 0),
            'like_count': info.get('like_count', 0),
            'tags': info.get('tags', []),
        }


def _get_video_transcript(video_id: str, include_timestamps: bool = True) -> str:
    """
    Fetch video transcript using youtube-transcript-api.

    Args:
        video_id: YouTube video ID
        include_timestamps: If True, format as "[mm:ss], text". If False, text only.

    Returns:
        Formatted transcript string
    """
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)

        try:
            transcript = transcript_list.find_transcript(['en'])
        except NoTranscriptFound:
            # Fall back to any available transcript
            available_languages = list(transcript_list._manually_created_transcripts.keys()) + \
                                list(transcript_list._generated_transcripts.keys())
            if available_languages:
                transcript = transcript_list.find_transcript([available_languages[0]])
            else:
                raise NoTranscriptFound(f"No transcripts available for video {video_id}")

        # Fetch the transcript entries
        entries = transcript.fetch()

        # Format with or without timestamps
        formatted_lines = []
        for entry in entries:
            if include_timestamps:
                timestamp = entry.start
                minutes = int(timestamp // 60)
                seconds = int(timestamp % 60)
                text = entry.text
                formatted_lines.append(f"[{minutes:02d}:{seconds:02d}], {text}")
            else:
                formatted_lines.append(entry.text)

        return '\n'.join(formatted_lines)

    except TranscriptsDisabled:
        raise Exception(f"Transcripts are disabled for video {video_id}")
    except NoTranscriptFound:
        raise Exception(f"No transcript found for video {video_id}")
    except Exception as e:
        raise Exception(f"Error fetching transcript: {str(e)}")


@tool
def analyze_youtube_video(url: str) -> str:
    """
    Extract transcript and metadata from YouTube video.

    Use this tool to analyze YouTube videos by fetching their transcripts
    and metadata (title, description, duration, views, etc.).

    Args:
        url: YouTube video URL (any standard format)

    Returns:
        Formatted analysis including metadata and full transcript
    """
    try:
        # Extract video ID
        video_id = _extract_video_id(url)

        # Fetch metadata
        metadata = _get_video_metadata(video_id)

        # Fetch transcript
        transcript = _get_video_transcript(video_id)

        # Format response
        response = f"""# Video Information
Title: {metadata['title']}
Uploader: {metadata['uploader']}
Duration: {metadata['duration']} seconds
Views: {metadata['view_count']:,}
Upload Date: {metadata['upload_date']}

## Description
{metadata['description'][:500]}{'...' if len(metadata['description']) > 500 else ''}

## Tags
{', '.join(metadata['tags'][:10]) if metadata['tags'] else 'None'}

## Full Transcript
{transcript}
"""

        return response

    except ValueError as e:
        return f"Error: Invalid YouTube URL - {str(e)}"
    except Exception as e:
        return f"Error analyzing video: {str(e)}"


# ============================================================================
# WEB PAGE FETCHING
# ============================================================================

@tool
def fetch_web_page(url: str) -> str:
    """
    Fetch and parse a web page, converting HTML to clean readable text.

    Works with articles, blog posts, Substack pages, and most web content.
    Removes navigation, scripts, and other non-content elements.

    Args:
        url: URL of the web page to fetch

    Returns:
        Clean markdown-formatted text content of the page
    """
    try:
        # Validate URL
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return f"Invalid URL: {url}"

        # Fetch page with browser-like headers to avoid 403 errors
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove non-content elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()

        # Convert to markdown
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.body_width = 0  # Don't wrap text

        text = h.handle(str(soup))

        # Clean up excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()

        # Truncate if too long (keep first 10000 chars)
        if len(text) > 20000:
            text = text[:20000] + "\n\n[Content truncated...]"

        return text

    except requests.exceptions.RequestException as e:
        return f"Error fetching web page: {str(e)}"
    except Exception as e:
        return f"Error parsing web page: {str(e)}"


# ============================================================================
# WEB SEARCH
# ============================================================================

@tool
def better_web_search(query: str) -> dict:
    """
    Perform web search using Serper API.

    Returns search results including organic results and knowledge graph
    when available. Useful for fact-checking and finding supporting evidence.

    Args:
        query: Search query string

    Returns:
        Dictionary with:
        - organic: List of search results (title, link, snippet)
        - knowledgeGraph: Key information box (if available)
    """
    url = "https://google.serper.dev/search"

    payload = json.dumps({
        "q": query,
        "gl": "us"  # Using US for better fact-checking sources
    })

    headers = {
        'X-API-KEY': os.getenv("SERPER_API_KEY"),
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, data=payload)
    return response.json()
