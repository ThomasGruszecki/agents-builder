from __future__ import annotations

import asyncio
import subprocess as sp
import os

from openai import AsyncOpenAI
from agents import (
    set_tracing_disabled,
    set_default_openai_client,
    set_default_openai_api,
    ItemHelpers,
    TResponseInputItem,
)
from util import RetryRunner, MAX_RETRIES, RETRY_BASE_DELAY

# Configuration
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
API_KEY = os.environ.get(
    "GEMINI_API_KEY"
)  # Set your API key here or use environment variables
MODEL_NAME = "gemini-2.0-flash-exp"

# Initialize the OpenAI client with retry options
client = AsyncOpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
    timeout=60.0,  # Increase timeout for longer operations
    max_retries=MAX_RETRIES,
)

set_default_openai_client(client=client, use_for_tracing=False)
set_default_openai_api("chat_completions")
set_tracing_disabled(disabled=True)

if __name__ == "__main__":

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
