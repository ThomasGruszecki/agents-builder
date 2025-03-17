# This one was written on my own without any AI, so I'm keeping it here as a testament to my initial understanding of the SDK.

from __future__ import annotations

import asyncio
import subprocess as sp
import os

from openai import AsyncOpenAI
from agents_test import Agent, Runner, set_tracing_disabled, set_default_openai_client, set_default_openai_api, ItemHelpers, TResponseInputItem, function_tool
from dataclasses import dataclass
from typing import Literal

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
API_KEY = os.environ.get('GEMINI_API_KEY') 
MODEL_NAME = "gemini-2.0-flash"
client = AsyncOpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
)
set_default_openai_client(client=client, use_for_tracing=False)
set_default_openai_api("chat_completions")
set_tracing_disabled(disabled=True)

@function_tool
def list_directory_tool(path: str) -> list[str]:
    """Return a list of files in the given directory."""
    print(f"Listing directory: {path}")
    try:
        return os.listdir(path)
    except Exception as e:
        print(f"Error listing directory: {str(e)}")
        return f"Error: {str(e)}"

@function_tool
def print_working_directory_tool() -> str:
    """Return the current working directory."""
    print(f"Printing working directory")
    try:
        return os.getcwd()
    except Exception as e:
        print(f"Error getting working directory: {str(e)}")
        return f"Error: {str(e)}"

@function_tool
def read_file_tool(path: str) -> str:
    """Return the contents of the given file."""
    print(f"Reading file: {path}")
    try:
        with open(path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"File not found: {path}")
        return f"Error: File '{path}' not found"
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        return f"Error reading file: {str(e)}"

@function_tool
def write_file_tool(path: str, content: str) -> None:
    """Write the given content to the given file."""
    print(f"Writing file: {path}")
    try:
        with open(path, "w") as f:
            f.write(content)
    except Exception as e:
        print(f"Error writing file: {str(e)}")
        return f"Error writing file: {str(e)}"
    
@function_tool
def ask_clarifying_questions_tool(question: str) -> str:
    """Ask the user a clarifying question. Use this only if you've already tried and failed to solve the problem with the available information."""
    return input(question + ": ")

@dataclass
class EvaluationFeedback:
    score: Literal["pass", "needs_improvement", "fail"]
    feedback: str

orchestrator_agent = Agent(
    name="orchestrator_agent",
    instructions=(
        "You are a helpful agent with a team of agents as tools. Take initiative to solve the user's problem with the information available. "
        "Use this process to solve problems:\n"
        "1. Use the planning_agent to understand the problem and create a detailed plan\n"
        "2. Use the coding_agent to implement the solution based on the plan\n"
        "3. Test the solution and iterate if needed\n"
        "Before asking clarifying questions, try to make reasonable assumptions and use your tools to explore. "
        "First check the current working directory, then list its contents, and read any files that seem relevant. "
        "Only ask for clarification if you've already tried and failed to solve the problem with the available information."
    ),
    tools= [
        list_directory_tool, 
        print_working_directory_tool, 
        read_file_tool,
        ask_clarifying_questions_tool,
        write_file_tool
    ],
    model=MODEL_NAME
)

evaluator = Agent[None](
    name="evaluator",
    instructions=(
        "Evaluate an agent's response against the user's request."
        + "If the response fails to satisfy the user's request, provide feedback on what needs to be improved and a hint on how to improve it."
        + "If the agent is taking too long to solve the problem, fail them."
    ),
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