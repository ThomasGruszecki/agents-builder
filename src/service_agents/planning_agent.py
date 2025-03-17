from agents import Agent
from tools import (
    list_directory_tool,
    print_working_directory_tool,
    read_file_tool,
    search_files_tool,
)
from util import prompt_with_agent_as_tool, ProgressTracker
prompt = """
You are a senior software engineer who excels at planning and designing software solutions.
    
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
"""


# Agent definitions with improved instructions
def getPlanningAgent(model_name: str = "gemini-2.0-flash-exp"):
    return Agent[ProgressTracker](
        name="planning_agent",
        instructions=prompt_with_agent_as_tool(prompt),
        tools=[
            list_directory_tool,
            print_working_directory_tool,
            read_file_tool,
            search_files_tool,
        ],
        model=model_name,
    )
