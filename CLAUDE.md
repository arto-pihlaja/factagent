# Fact-Checker Application

## Project Overview

An agentic fact-checking system built on smolagents that summarizes web resources and optionally performs fact-checking of claims found in the content.

**Deployment Target**: Hugging Face Spaces (Python 3.10 container)

---

## Use Cases

### Example 1: YouTube Video Summary
- **Input**: YouTube URL
- **Output**: Summary of video transcript with key points

### Example 2: Web Article with Fact-Checking
- **Input**: Substack article URL + fact-check flag enabled
- **Output**:
  - Summary of article content
  - Key claims extracted from article
  - Verification results with supporting/contradicting sources

---

## Architecture

### Single-Agent Design (MVP)

```
┌─────────────────────────────────────┐
│   Fact-Checker Agent (CodeAgent)   │
│   Model: OpenRouter API             │
│                                     │
│  Workflow:                          │
│  1. Parse user input                │
│  2. Retrieve content (YouTube/web)  │
│  3. Summarize content               │
│  4. Optional: fact-check claims     │
│  5. Return formatted results        │
└─────────────────────────────────────┘
              ↓ uses
┌─────────────────────────────────────┐
│         Tool Suite                  │
│                                     │
│ • analyze_youtube_video             │
│   - Extract transcripts             │
│   - Get metadata                    │
│                                     │
│ • fetch_web_page                    │
│   - HTML to markdown conversion     │
│   - Clean text extraction           │
│                                     │
│ • better_web_search                 │
│   - Serper API integration          │
│   - Find supporting/contradicting   │
│     evidence for claims             │
└─────────────────────────────────────┘
```

### Why Single Agent?

- **Simplicity**: Sequential workflow (retrieve → summarize → verify)
- **Fast Development**: Reuse existing tools from course_final_ass
- **Lower Costs**: Fewer LLM calls for MVP
- **Easy Debugging**: Single execution trace
- **Proven Pattern**: Based on successful course_final_ass implementation

### Future: Multi-Agent Migration

Migrate when:
- Context usage regularly exceeds 50% of model limit
- Need to parallelize multiple independent fact-checks
- Quality improvements require specialized agents

---

## Technology Stack

### Core Framework
- **smolagents 1.22.0**: Agent orchestration
- **Python 3.10**: HF Spaces requirement

### LLM Provider
- **OpenRouter**: Primary and only provider for MVP
- **Model**: `anthropic/claude-3.5-sonnet` (configurable)

### Content Retrieval
- **youtube-transcript-api**: YouTube transcripts
- **yt-dlp**: YouTube metadata
- **beautifulsoup4**: HTML parsing
- **html2text**: Markdown conversion

### Web Search
- **Serper API**: Search for fact-checking evidence

### UI Framework
- **Gradio 5.49.1**: Web interface
- **HF Spaces**: Deployment platform

---

## Project Structure

```
/hfagents/factchecker/
├── CLAUDE.md              # This file - project documentation
├── .env.example           # Environment variable template
├── .gitignore            # Git ignore rules
├── README.md             # HF Spaces configuration
├── requirements.txt      # Python dependencies
├── config.py             # OpenRouter configuration
├── tools.py              # Tool implementations (reused from course_final_ass)
├── agent.py              # Main fact-checker agent
└── app.py                # Gradio UI
```

---

## Configuration

### Environment Variables

Required:
- `OPENROUTER_API_KEY`: OpenRouter API key
- `SERPER_API_KEY`: Serper API key for web search

Optional:
- `MODEL_ID`: Override default model (default: `anthropic/claude-3.5-sonnet`)

### Model Configuration

**config.py** handles:
- OpenRouter client initialization
- Model ID selection
- API key validation

**Simple, no fallbacks** - OpenRouter only for MVP

---

## Tools

### 1. analyze_youtube_video

**Purpose**: Extract YouTube video transcripts and metadata

**Input**: YouTube URL

**Output**:
```python
{
    "transcript": "Full transcript with timestamps...",
    "metadata": {
        "title": "Video title",
        "description": "Video description",
        "duration": "PT10M30S",
        "views": 123456,
        "upload_date": "2025-01-01"
    }
}
```

**Implementation**: Reused from `course_final_ass/video_tools.py`

---

### 2. fetch_web_page

**Purpose**: Extract clean text content from web pages

**Input**: URL

**Output**: Markdown-formatted page content (max 10,000 chars)

**Features**:
- HTML to Markdown conversion
- Removes scripts, styles, navigation
- Preserves article structure
- Handles Substack and common blog platforms

**Implementation**: Reused from `course_final_ass/tools.py`

---

### 3. better_web_search

**Purpose**: Search web for fact-checking evidence

**Input**: Search query string

**Output**: List of search results with titles, snippets, URLs

**Provider**: Serper API

**Implementation**: Reused from `course_final_ass/tools.py`

---

## Agent Design

### CodeAgent Configuration

```python
agent = CodeAgent(
    tools=[analyze_youtube_video, fetch_web_page, better_web_search],
    model=openrouter_model,
    max_steps=15,
    additional_authorized_imports=["json", "re"]
)
```

### Workflow

1. **Parse Input**
   - Extract URL from user input
   - Check fact-check flag

2. **Retrieve Content**
   - If YouTube: `analyze_youtube_video(url)`
   - Else: `fetch_web_page(url)`

3. **Summarize**
   - Generate concise summary (3-5 key points)
   - Identify main themes and arguments

4. **Fact-Check (Optional)**
   - Extract verifiable claims from content
   - For each claim:
     - Search for evidence: `better_web_search(claim + " fact check")`
     - Assess source reliability
     - Determine verdict: supported/contradicted/mixed/unverified
   - Return structured results

5. **Format Output**
   - Summary section
   - Optional: Fact-check results table

---

## Gradio UI

### Interface

**Inputs**:
- Text box: URL input
- Checkbox: "Enable fact-checking"

**Output**:
- Text area: Results (summary + optional fact-checks)

**Example**:
```
Summary:
- Key point 1
- Key point 2
- Key point 3

Fact-Check Results (if enabled):
Claim: "Statement from article"
Verdict: Supported
Confidence: High
Sources:
- [Reuters] Supporting article
- [AP News] Confirming report
```

---

## Development Roadmap

### Phase 1: MVP (Current)

**Week 1: Core Implementation**
- [x] Initialize project with CLAUDE.md
- [ ] Set up configuration (OpenRouter only)
- [ ] Copy tools from course_final_ass
- [ ] Create simple CodeAgent
- [ ] Build minimal Gradio UI

**Week 2: Testing & Deployment**
- [ ] Test YouTube summary
- [ ] Test web article summary
- [ ] Add basic fact-checking
- [ ] Deploy to HF Spaces

### Phase 2: Enhancement (Future)

**Incremental Improvements**:
- Advanced claim extraction
- Source reliability scoring
- Multiple claim verification in parallel
- UI improvements (formatted results, progress indicators)
- Caching for repeated queries

### Phase 3: Multi-Agent (If Needed)

**Migration Triggers**:
- Context usage > 50% regularly
- Need for specialized analysis
- Performance/quality plateau

**Architecture**:
- Orchestrator agent
- Content retriever agent
- Summarizer agent
- Fact-checker agent

---

## Testing Strategy

### Manual Testing

1. **YouTube Video Summary**
   - Test URL: Popular educational video
   - Verify transcript extraction
   - Check summary quality

2. **Web Article Summary**
   - Test URL: Substack article
   - Verify content extraction
   - Check summary accuracy

3. **Fact-Checking**
   - Test URL: Article with verifiable claims
   - Enable fact-check flag
   - Verify claim extraction
   - Check evidence sources

### Success Criteria

- Summaries capture key points (3-5 bullet points)
- YouTube transcripts extracted correctly
- Web pages converted to clean text
- Fact-checks reference reliable sources
- Response time < 30s (summary), < 60s (with fact-checking)

---

## Deployment

### HF Spaces Configuration

**README.md** header:
```yaml
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
```

### Secrets

Set in HF Spaces settings:
- `OPENROUTER_API_KEY`
- `SERPER_API_KEY`

### Requirements

See `requirements.txt` - minimal dependencies for MVP

---

## Known Limitations (MVP)

1. **Context Window**: Long transcripts may exceed model limits
   - Mitigation: Truncate or chunk if needed

2. **Fact-Check Accuracy**: LLM-based verification may have errors
   - Mitigation: Confidence scores, multiple sources required

3. **Rate Limits**: API rate limits may affect high usage
   - Mitigation: Caching, rate limiting on UI

4. **Source Coverage**: Limited to web-searchable content
   - Mitigation: Clear disclaimer about limitations

---

## Future Enhancements

### Short-term
- PDF article support
- Better claim extraction (structured prompts)
- Source reliability whitelist/scoring
- Improved UI formatting

### Long-term
- Multi-agent architecture (if needed)
- Parallel fact-checking
- Custom source database
- User feedback loop for quality improvement
- API endpoint for programmatic access

---

## References

**Based on**:
- `/hfagents/course_final_ass/` - Existing working implementation
- smolagents documentation - Agent framework
- HF Spaces - Deployment platform

**Key Learnings**:
- Single agent sufficient for sequential workflows
- Reuse proven patterns from course_final_ass
- Start simple, iterate based on usage data

---

## Development Notes

### Code Style
- Type hints for function signatures
- Docstrings for all tools
- Clear error handling with informative messages
- Environment variables for all secrets

### Best Practices
- Test locally before deploying
- Use .env.example as template
- Keep tools focused and single-purpose
- Log important operations for debugging
- Graceful degradation on API failures

---

## Changelog

### 2025-11-05: Project Initialization
- Created CLAUDE.md
- Defined single-agent architecture
- Planned incremental MVP build
- OpenRouter-only configuration for simplicity

---

*This document serves as the primary context for Claude Code sessions working on this project.*
