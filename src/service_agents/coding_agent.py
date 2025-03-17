from agents import Agent
from tools import (
    list_directory_tool,
    print_working_directory_tool,
    read_file_tool,
    search_files_tool,
    grep_tool,
    semantic_patch_file_tool,
    run_command_tool,
    create_directory_tool,
    edit_file_tool,
)
from util import prompt_with_agent_as_tool, ProgressTracker

prompt = """
You are a senior software engineer who excels at writing high-quality, maintainable code.
        
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
        """

def getCodingAgent(model_name: str = "gemini-2.0-flash-exp"):
    return Agent[ProgressTracker](
        name="coding_agent",
        instructions=prompt_with_agent_as_tool(prompt),
        tools=[
            list_directory_tool,
            print_working_directory_tool,
            read_file_tool,
            search_files_tool,
            grep_tool,
            semantic_patch_file_tool,
            run_command_tool,
            create_directory_tool,
            edit_file_tool,
        ],
        model=model_name,
    )
