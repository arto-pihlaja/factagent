"""
Configuration for Fact-Checker Agent
OpenRouter-only setup for MVP
"""

import os
from dotenv import load_dotenv
from smolagents import LiteLLMModel

# Load environment variables
load_dotenv()

def get_model():
    """
    Initialize and return OpenRouter model via LiteLLM.

    Returns:
        LiteLLMModel: Configured model for agent

    Raises:
        ValueError: If OPENROUTER_API_KEY is not set
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY not found in environment variables. "
            "Please set it in .env file or environment."
        )

    # Get model ID from env or use default
    # Use openrouter/ prefix to tell LiteLLM to route through OpenRouter
    model_id = os.getenv("MODEL_ID", "openrouter/anthropic/claude-3.5-sonnet")

    # Create LiteLLM model configured for OpenRouter
    model = LiteLLMModel(
        model_id=model_id,
        api_key=api_key,
        timeout=120
    )

    return model


def get_serper_api_key():
    """
    Get Serper API key for web search.

    Returns:
        str: Serper API key

    Raises:
        ValueError: If SERPER_API_KEY is not set
    """
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        raise ValueError(
            "SERPER_API_KEY not found in environment variables. "
            "Please set it in .env file or environment."
        )
    return api_key
