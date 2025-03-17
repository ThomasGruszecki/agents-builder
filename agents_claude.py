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

# Code analysis tools
@function_tool
def analyze_code_tool(code: str, language: str = "python") -> Dict[str, Any]:
    """
    Analyze code for potential issues or improvements.
    
    Args:
        code: The code to analyze.
        language: The programming language of the code.
        
    Returns:
        A dictionary with analysis results.
    """
    # This is a simplified analyzer - in a real system you'd use language-specific linters
    issues = []
    
    if language.lower() == "python":
        # Check for basic Python issues
        if "except:" in code and "except Exception" not in code:
            issues.append({
                "type": "bare_except",
                "message": "Bare except clause found. Consider catching specific exceptions.",
                "severity": "warning"
            })
        
        if "import *" in code:
            issues.append({
                "type": "wildcard_import",
                "message": "Wildcard import found. Consider importing specific names.",
                "severity": "warning"
            })
            
        # Check for hardcoded credentials
        if any(pattern in code for pattern in ["api_key", "password", "secret", "token"]):
            issues.append({
                "type": "hardcoded_credentials",
                "message": "Possible hardcoded credentials found. Consider using environment variables.",
                "severity": "error"
            })
    
    return {
        "issues": issues,
        "issue_count": len(issues),
        "suggestions": [issue["message"] for issue in issues],
        "error": None
    }

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
    output_type=EvaluationFeedback,
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
        analyze_code_tool,
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
        ask_clarifying_questions_tool
    ],
    model=MODEL_NAME
)

evaluator = Agent(
    name="evaluator",
    instructions="""You are a senior software engineering manager who evaluates the quality of solutions.

Your evaluation criteria:
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

Your evaluation should result in one of three scores:
- "pass": The solution completely meets requirements with high quality
- "needs_improvement": The solution is close but requires specific enhancements
- "fail": The solution has fundamental flaws that require a significant rework

Be decisive but fair in your assessment. Include detailed reasoning for your score.
""",
    output_type=EvaluationFeedback,
    model=MODEL_NAME
)


# Add retry mechanism for API calls
async def retry_with_exponential_backoff(
    func: Callable,
    *args,
    max_retries: int = MAX_RETRIES,
    base_delay: float = RETRY_BASE_DELAY,
    **kwargs
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
            
            delay = base_delay * (2 ** retries) + (0.1 * random.random())
            retries += 1
            
            print(f"Rate limited. Retrying in {delay:.2f} seconds... (Attempt {retries}/{max_retries})")
            await asyncio.sleep(delay)
        except (APIError, Exception) as e:
            error_code = getattr(e, "code", None)
            status_code = getattr(e, "status_code", None)
            
            # Only retry on certain error types
            if (status_code and status_code >= 500) or error_code in ["server_error", "timeout"]:
                if retries >= max_retries:
                    print(f"API error after {max_retries} retries. Giving up.")
                    raise
                
                delay = base_delay * (2 ** retries) + (0.1 * random.random())
                retries += 1
                
                error_message = str(e)
                print(f"API error: {error_message}. Retrying in {delay:.2f} seconds... (Attempt {retries}/{max_retries})")
                await asyncio.sleep(delay)
            else:
                # Don't retry other errors
                raise

# Override the Runner class to add retry functionality
class RetryRunner:
    """
    Runner that includes retry logic for rate limits and API errors.
    """
    @staticmethod
    async def run(agent, input_items, **kwargs):
        """Run an agent with retry logic for rate limits."""
        return await retry_with_exponential_backoff(
            Runner.run,
            agent,
            input_items,
            **kwargs
        )

async def main():
    """
    Main function that manages the agent workflow.
    
    This includes:
    1. Initial problem understanding
    2. Solution planning and implementation
    3. Evaluation and iteration
    4. Final solution delivery
    """
    # Welcome message and initial project gathering
    print("\n" + "="*60)
    print("🤖 Senior Developer Agent Assistant 🤖".center(60))
    print("="*60 + "\n")
    
    print("I'll help you with software development tasks by using a team of specialized agents.")
    print("Let me know what you need help with, and I'll coordinate the right specialists to solve it.\n")
    
    # Get initial request
    msg = input("What software development task can I help you with? ")
    input_items: list[TResponseInputItem] = [{"content": msg, "role": "user"}]
    
    # Track progress
    latest: str | None = None
    result: EvaluationFeedback | None = None
    iteration_count = 0
    max_iterations = 5  # Prevent infinite loops
    
    try:
        print("\n📋 Analyzing your request and gathering context...\n")
        
        # Main solution development loop
        while (not result or result.score == "needs_improvement") and iteration_count < max_iterations:
            iteration_count += 1
            
            print(f"\n📝 Working on solution (Iteration {iteration_count}/{max_iterations})...")
            
            # Run the orchestrator with retry logic
            try:
                orchestrator_result = await RetryRunner.run(
                    orchestrator_agent, 
                    input_items
                )
                
                input_items = orchestrator_result.to_input_list()
                latest = ItemHelpers.text_message_outputs(orchestrator_result.new_items)
                
                print(f"\n✨ Current solution progress:\n{'-'*60}\n{latest}\n{'-'*60}")
                
            except Exception as e:
                print(f"\n❌ Error during orchestration: {str(e)}")
                if iteration_count >= max_iterations // 2:
                    # If we've already tried multiple times, continue with what we have
                    print("Continuing with partial solution...")
                    if not latest:
                        print("No solution available. Please try again.")
                        return
                else:
                    # Add error context and retry
                    error_message = f"The previous attempt encountered an error: {str(e)}. Please try a different approach."
                    input_items.append({"content": error_message, "role": "user"})
                    continue
            
            # Evaluate the solution
            try:
                evaluator_result = await RetryRunner.run(evaluator, input_items)
                result: EvaluationFeedback = evaluator_result.final_output
                
                print(f"\n🔍 Evaluation Score: {result.score}")
                print(f"📊 Feedback: {result.feedback}")
                
                # Add feedback for the next iteration if needed
                if result.score == "needs_improvement" and iteration_count < max_iterations:
                    input_items.append({"content": f"Please address this feedback: {result.feedback}", "role": "user"})
                    print("\n🔄 Refining solution based on feedback...\n")
                
            except Exception as e:
                print(f"\n❌ Error during evaluation: {str(e)}")
                # If evaluation fails but we have a solution, continue
                if latest:
                    print("Continuing with current solution...")
                    result = EvaluationFeedback(score="pass", feedback="Evaluation failed, but solution is available.")
                else:
                    print("No solution available. Please try again.")
                    return
        
        # Final solution delivery
        print("\n" + "="*60)
        if result.score == "pass":
            print("✅ FINAL SOLUTION COMPLETE")
        elif iteration_count >= max_iterations:
            print("⚠️ MAXIMUM ITERATIONS REACHED")
        else:
            print("⚠️ SOLUTION NEEDS IMPROVEMENT")
        print("="*60 + "\n")
        
        print(f"{latest}\n")
        
        # Get feedback for continuous improvement
        feedback = input("\nWould you like to provide feedback on this solution? (optional): ")
        if feedback.strip():
            print("\nThank you for your feedback! I'll use it to improve future solutions.")
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user. Exiting...")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {str(e)}")
        # Try to provide partial solution if available
        if latest:
            print("\nHere's the partial solution I was able to develop:")
            print(f"\n{latest}\n")

if __name__ == "__main__":
    # Add missing imports
    import random
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nFatal error: {str(e)}")