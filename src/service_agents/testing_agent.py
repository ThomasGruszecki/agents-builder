from agents import Agent
from tools import (
    list_directory_tool,
    read_file_tool,
    grep_tool,
    run_command_tool,
    semantic_patch_file_tool,
    create_directory_tool,
    create_file_tool
)
from util import prompt_with_agent_as_tool
from hook import CustomAgentHooks

prompt = """
You are a senior software engineer who excels at testing and quality assurance.
    
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

Use the create file tool exclusively to create unit tests.
If needed, use uv to install dependencies.
"""


def getTestingAgent(model_name: str = "gemini-2.0-flash-exp"):
    return Agent(
        name="testing_agent",
        instructions=prompt_with_agent_as_tool(prompt),
        tools=[
            list_directory_tool,
            read_file_tool,
            run_command_tool,
            grep_tool,
            create_directory_tool,
            create_file_tool
        ],
        hooks=CustomAgentHooks("Testing"),
        model=model_name,
    )
