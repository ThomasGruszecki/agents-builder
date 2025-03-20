import asyncio
import random
from typing import Callable
from openai import APIError, RateLimitError
from agents import Runner

# Constants
MAX_RETRIES = 3
RETRY_BASE_DELAY = 6  # seconds

async def retry_with_exponential_backoff(
    func: Callable,
    *args,
    max_retries: int = MAX_RETRIES,
    base_delay: float = RETRY_BASE_DELAY,
    **kwargs,
):
    """
    Retry a function with exponential backoff when rate limited.

    Args:
        func: The async function to call
        *args: Arguments to pass to the function
        max_retries: Maximum number of retries
        base_delay: Base delay between retries in seconds
        **kwargs: Keyword arguments to pass to the function

    Returns:
        The result of the function call
    """
    retries = 0

    while True:
        try:
            return await func(*args, **kwargs)
        except RateLimitError as e:
            if retries >= max_retries:
                print(f"Rate limit exceeded after {max_retries} retries. Giving up.")
                raise

            delay = base_delay * (2**retries) + (0.1 * random.random())
            retries += 1

            print(
                f"Rate limited. Retrying in {delay:.2f} seconds... (Attempt {retries}/{max_retries})"
            )
            await asyncio.sleep(delay)
        except (APIError, Exception) as e:
            error_code = getattr(e, "code", None)
            status_code = getattr(e, "status_code", None)

            # Only retry on certain error types
            if (status_code and status_code >= 500) or error_code in [
                "server_error",
                "timeout",
            ]:
                if retries >= max_retries:
                    print(f"API error after {max_retries} retries. Giving up.")
                    raise

                delay = base_delay * (2**retries) + (0.1 * random.random())
                retries += 1

                error_message = str(e)
                print(
                    f"API error: {error_message}. Retrying in {delay:.2f} seconds... (Attempt {retries}/{max_retries})"
                )
                await asyncio.sleep(delay)
            else:
                # Don't retry other errors
                raise

class RetryRunner:
    """
    Runner that includes retry logic for rate limits and API errors.
    """

    @staticmethod
    async def run(agent, input_items, **kwargs):
        """Run an agent with retry logic for rate limits."""
        return await retry_with_exponential_backoff(
            Runner.run, agent, input_items, **kwargs
        )
