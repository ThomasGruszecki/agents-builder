from __future__ import annotations

import asyncio
import subprocess as sp
import os
import time
import json
import sys
from typing import Literal, Dict, List, Any, Optional, Union, Callable, TypeVar, Generic, Tuple
from dataclasses import dataclass, field

from openai import AsyncOpenAI, APIError, RateLimitError
from agents import Agent, Runner, set_tracing_disabled, set_default_openai_client, set_default_openai_api, ItemHelpers, TResponseInputItem, function_tool

# Configuration
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
API_KEY = os.environ.get('GEMINI_API_KEY')  # Set your API key here or use environment variables
MODEL_NAME = "gemini-2.0-flash"

# Retry configuration
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2  # seconds

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

# Enhanced file system tools
@function_tool
def list_directory_tool(path: str = ".") -> Dict[str, Any]:
    """
    Return detailed information about files in the given directory.

    Args:
        path: The directory path to list. Defaults to current directory.

    Returns:
        A dictionary with files, directories, and any errors.
    """
    try:
        items = os.listdir(path)
        result = {
            "files": [],
            "directories": [],
            "error": None
        }

        for item in items:
            item_path = os.path.join(path, item)
            try:
                if os.path.isfile(item_path):
                    result["files"].append({
                        "name": item,
                        "size": os.path.getsize(item_path),
                        "extension": os.path.splitext(item)[1],
                        "modified": os.path.getmtime(item_path)
                    })
                elif os.path.isdir(item_path):
                    result["directories"].append(item)
            except Exception as e:
                # Skip items with permission issues
                pass

        return result
    except Exception as e:
        return {"error": str(e), "files": [], "directories": []}

@function_tool
def print_working_directory_tool() -> Dict[str, Any]:
    """Return the current working directory."""
    try:
        return {"path": os.getcwd(), "error": None}
    except Exception as e:
        return {"error": str(e), "path": None}

@function_tool
def read_file_tool(path: str) -> Dict[str, Any]:
    """
    Read and return the contents of the given file.

    Args:
        path: The path to the file to read.

    Returns:
        A dictionary with the file content or an error message.
    """
    try:
        with open(path, 'r') as f:
            content = f.read()

        # Add file metadata
        file_size = os.path.getsize(path)
        file_extension = os.path.splitext(path)[1]

        return {
            "content": content,
            "size": file_size,
            "extension": file_extension,
            "error": None
        }
    except FileNotFoundError:
        return {"error": f"File '{path}' not found", "content": None}
    except Exception as e:
        return {"error": str(e), "content": None}

@function_tool
def write_file_tool(path: str, content: str) -> Dict[str, Any]:
    """
    Write content to a file.

    Args:
        path: The path where the file should be written.
        content: The content to write to the file.

    Returns:
        A dictionary indicating success or failure.
    """
    try:
        with open(path, "w") as f:
            f.write(content)
        return {"success": True, "error": None}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Additional software development tools
@function_tool
def run_command_tool(command: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Run a shell command and return the result.

    Args:
        command: The command to run.
        timeout: Maximum time in seconds to wait for the command to complete.

    Returns:
        A dictionary with stdout, stderr, and return code.
    """
    try:
        result = sp.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "error": None
        }
    except sp.TimeoutExpired:
        return {"error": f"Command timed out after {timeout} seconds"}
    except Exception as e:
        return {"error": str(e)}

@function_tool
def search_files_tool(pattern: str, path: str = ".", recursive: bool = True) -> Dict[str, Any]:
    """
    Search for files matching a pattern.

    Args:
        pattern: The pattern to search for (supports glob syntax).
        path: The directory to search in.
        recursive: Whether to search recursively.

    Returns:
        A dictionary with matching files.
    """
    try:
        import glob

        search_pattern = os.path.join(path, "**", pattern) if recursive else os.path.join(path, pattern)
        matches = glob.glob(search_pattern, recursive=recursive)

        return {
            "matches": matches,
            "count": len(matches),
            "error": None
        }
    except Exception as e:
        return {"error": str(e), "matches": []}

@function_tool
def grep_tool(pattern: str, file_path: str) -> Dict[str, Any]:
    """
    Search for a pattern in a file.

    Args:
        pattern: The pattern to search for.
        file_path: The file to search in.

    Returns:
        A dictionary with matching lines.
    """
    try:
        import re
        matches = []

        with open(file_path, 'r') as f:
            for i, line in enumerate(f, 1):
                if re.search(pattern, line):
                    matches.append({"line_number": i, "content": line.rstrip()})

        return {
            "matches": matches,
            "count": len(matches),
            "error": None
        }
    except FileNotFoundError:
        return {"error": f"File '{file_path}' not found", "matches": []}
    except Exception as e:
        return {"error": str(e), "matches": []}

@function_tool
def ask_clarifying_questions_tool(question: str) -> str:
    """
    Ask the user a clarifying question.

    Only use this when you've exhausted all available information and tools.
    First try to make reasonable assumptions or use other tools to find needed information.

    Args:
        question: The question to ask the user.

    Returns:
        The user's response.
    """
    return input(question + ": ")

# Project structure and code management tools
@function_tool
def create_directory_tool(path: str) -> Dict[str, Any]:
    """
    Create a new directory.

    Args:
        path: The directory path to create.

    Returns:
        A dictionary indicating success or failure.
    """
    try:
        os.makedirs(path, exist_ok=True)
        return {"success": True, "error": None}
    except Exception as e:
        return {"success": False, "error": str(e)}

@dataclass
class EvaluationFeedback:
    score: Literal["pass", "needs_improvement", "fail"]
    feedback: str

# Agent definitions with improved instructions
planning_agent = Agent(
    name="planning_agent",
    instructions="""You are a senior software engineer who excels at planning and designing software solutions.

Your responsibilities:
1. Analyze the requirements thoroughly
2. Identify potential challenges and edge cases
3. Create a clear, step-by-step plan to implement the solution
4. Break down complex tasks into manageable subtasks
5. Set clear success criteria to evaluate the final solution

When creating your plan:
- Be specific about implementation details
- Provide clear reasons for design decisions
- Consider trade-offs between different approaches
- Anticipate potential issues and provide mitigation strategies
- Structure your plan in clear, numbered steps

Always start by gathering all available context before creating your plan.
If critical information is missing, note it but continue with reasonable assumptions.
""",
    tools=[
        list_directory_tool,
        print_working_directory_tool,
        read_file_tool,
        search_files_tool,
    ],
    model=MODEL_NAME
)

coding_agent = Agent(
    name="coding_agent",
    instructions="""You are a senior software engineer who excels at writing high-quality, maintainable code.

Your responsibilities:
1. Implement solutions according to the provided plan
2. Write clean, efficient, and well-documented code
3. Follow best practices for the programming language being used
4. Provide extensive error handling and logging
5. Write testable code with appropriate modularization

When writing code:
- Follow consistent coding standards and patterns
- Add comprehensive docstrings and comments
- Include proper error handling for all edge cases
- Use meaningful variable and function names
- Structure code for readability and maintainability
- Avoid hardcoding values that might need to change

Always start by understanding the requirements and plan completely before writing code.
When faced with implementation decisions, choose the option that prioritizes reliability and maintainability.
""",
    tools=[
        list_directory_tool,
        print_working_directory_tool,
        read_file_tool,
        write_file_tool,
        search_files_tool,
        grep_tool,
        run_command_tool,
        create_directory_tool,
    ],
    model=MODEL_NAME
)

testing_agent = Agent(
    name="testing_agent",
    instructions="""You are a senior software engineer who excels at testing and quality assurance.

Your responsibilities:
1. Create comprehensive test plans for the implemented solution
2. Design test cases that cover happy paths and edge cases
3. Verify that the solution meets all requirements
4. Identify and report bugs or issues with the implementation
5. Suggest improvements to make the code more robust

When testing:
- Start with basic functionality tests
- Progressively test more complex scenarios
- Verify error handling and edge cases
- Check performance under expected load
- Validate that the solution meets all success criteria

Always provide clear, detailed reports of your findings, including:
- What was tested
- How it was tested
- Any issues discovered
- Recommendations for fixes or improvements
""",
    tools=[
        list_directory_tool,
        print_working_directory_tool,
        read_file_tool,
        write_file_tool,
        run_command_tool,
        grep_tool,
    ],
    model=MODEL_NAME
)

orchestrator_agent = Agent(
    name="orchestrator_agent",
    instructions="""You are a senior software engineering team lead who coordinates a team of specialized agents to solve complex programming tasks efficiently.

AVAILABLE SPECIALISTS:
- planning_agent: Creates detailed technical specifications and step-by-step plans
- coding_agent: Implements solutions following best practices and design patterns
- testing_agent: Verifies implementation quality and identifies issues

YOUR PROCESS:
1. UNDERSTAND THE PROBLEM:
    - Immediately explore the environment using directory and file tools
    - Gather all relevant information before proceeding

2. CREATE A PLAN:
    - Use planning_agent to develop a detailed implementation strategy
    - Review the plan to ensure it addresses all requirements

3. IMPLEMENT THE SOLUTION:
    - Use coding_agent to write high-quality, maintainable code
    - Provide clear guidance based on the approved plan

4. VERIFY AND REFINE:
    - Use testing_agent to verify the solution works as expected
    - Address any issues discovered during testing
    - Iterate until the solution fully meets requirements

IMPORTANT GUIDELINES:
- EXPLORE BEFORE ASKING: Always use available tools to gather information before asking clarifying questions
- BE RESOURCEFUL: Make reasonable assumptions when information is incomplete
- FOCUS ON EFFICIENCY: Minimize token usage by providing clear, specific instructions to specialist agents
- PROVIDE CONTEXT: When delegating to specialist agents, include all relevant information they need
- HANDLE ERRORS GRACEFULLY: Always check for errors in tool responses before proceeding

Your ultimate goal is to deliver production-quality solutions that meet all requirements with minimal guidance.
""",
    tools=[
        planning_agent.as_tool(tool_name="planning_agent", tool_description="Creates detailed technical specifications and step-by-step plans"),
        coding_agent.as_tool(tool_name="coding_agent", tool_description="Implements solutions following best practices and design patterns"),
        testing_agent.as_tool(tool_name="testing_agent", tool_description="Verifies implementation quality and identifies issues"),
        ask_clarifying_questions_tool,
    ],
    model=MODEL_NAME
)

# Custom exception for rate limit handling
class RateLimitException(Exception):
    """Exception raised when hitting API rate limits."""
    def __init__(self, message="Rate limit exceeded", retry_after=None):
        self.retry_after = retry_after
        super().__init__(message)

# Rate limit handling decorator
async def with_rate_limit_handling(func, *args, **kwargs):
    """Decorator to handle rate limit exceptions with exponential backoff."""
    retries = 0
    while True:
        try:
            return await func(*args, **kwargs)
        except RateLimitError as e:
            retries += 1
            if retries > MAX_RETRIES:
                raise Exception(f"Maximum retries ({MAX_RETRIES}) exceeded due to rate limits.")

            # Get retry time from response if available, otherwise use exponential backoff
            retry_after = getattr(e, "retry_after", None)
            if retry_after is None:
                retry_after = RETRY_BASE_DELAY * (2 ** (retries - 1))

            print(f"\n⚠️ Rate limit hit. Retrying in {retry_after} seconds... (Attempt {retries}/{MAX_RETRIES})")
            time.sleep(retry_after)
        except APIError as e:
            if "rate" in str(e).lower():
                # Handle other rate-related errors
                retries += 1
                if retries > MAX_RETRIES:
                    raise Exception(f"Maximum retries ({MAX_RETRIES}) exceeded due to API errors.")

                backoff = RETRY_BASE_DELAY * (2 ** (retries - 1))
                print(f"\n⚠️ API error (possibly rate-related). Retrying in {backoff} seconds... (Attempt {retries}/{MAX_RETRIES})")
                time.sleep(backoff)
            else:
                # Re-raise non-rate-related API errors
                raise

# Progress tracker
@dataclass
class ProgressTracker:
    start_time: float = field(default_factory=time.time)
    steps_completed: int = 0
    total_steps: int = 0
    current_stage: str = "initialization"

    def update(self, stage: str, steps_completed: int = None, total_steps: int = None):
        """Update the progress tracker."""
        self.current_stage = stage
        if steps_completed is not None:
            self.steps_completed = steps_completed
        if total_steps is not None:
            self.total_steps = total_steps

    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time

    def get_progress_report(self) -> str:
        """Get a formatted progress report."""
        elapsed = self.get_elapsed_time()
        minutes, seconds = divmod(int(elapsed), 60)
        hours, minutes = divmod(minutes, 60)

        if self.total_steps > 0:
            percentage = (self.steps_completed / self.total_steps) * 100
            progress = f"{percentage:.1f}% ({self.steps_completed}/{self.total_steps})"
        else:
            progress = f"{self.steps_completed} steps"

        return f"Stage: {self.current_stage} | Progress: {progress} | Time: {hours:02d}:{minutes:02d}:{seconds:02d}"

evaluator = Agent[EvaluationFeedback](
    name="evaluator",
    instructions="""You are a senior software engineering manager who evaluates the quality of solutions.

Your evaluation must result in one of three scores:
- "pass": The solution fully meets requirements with high quality
- "needs_improvement": The solution has shortcomings but is on the right track
- "fail": The solution has fundamental flaws or misses critical requirements

Provide detailed feedback explaining your score and specific recommendations for improvement.
If the agent has been working on the problem for too long without meaningful progress, fail them and recommend a different approach.
 criteria:
1. COMPLETENESS: Does the solution fully address all requirements?
2. CORRECTNESS: Is the implementation free of bugs and logical errors?
3. CODE QUALITY: Does the code follow best practices for maintainability?
4. EFFICIENCY: Is the solution optimized for performance and resource usage?
5. ROBUSTNESS: Does the solution handle edge cases and errors appropriately?

When evaluating:
- Be thorough but fair in your assessment
- Recognize both strengths and areas for improvement
- Provide specific, actionable feedback
- Include concrete examples when pointing out issues
- Suggest specific improvements rather than vague directions

Your evaluation should be concise and directly address the agent's last response in the context of the original user request. Focus on whether the agent is making progress towards a satisfactory solution.
""",
    output_type=EvaluationFeedback,
    model=MODEL_NAME
)

async def main():
    msg = input("Hi! What can I help you with? ")
    input_items: list[TResponseInputItem] = [{"content": msg, "role": "user"}]
    latest: str | None = None
    result: EvaluationFeedback | None = None

    while not result or result.score == "needs_improvement":
        orchestrator_result = await Runner.run(
            orchestrator_agent,
            input_items
        )

        input_items = orchestrator_result.to_input_list()
        latest = ItemHelpers.text_message_outputs(orchestrator_result.new_items)

        print(f"\nCurrent solution progress:\n{latest}")

        evaluator_result = await Runner.run(evaluator, input_items)
        result: EvaluationFeedback = evaluator_result.final_output

        input_items.append({"content": f"Feedback: {result.feedback}", "role": "user"})

        print(f"Evaluator says: {result.feedback}")
        print(f"Evaluator score: {result.score}")
        print("\n\n ----------")

    print(f"\n\nFinal response:\n{latest}")


if __name__ == "__main__":
    asyncio.run(main())