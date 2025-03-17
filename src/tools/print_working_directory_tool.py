import os
from typing import Dict, Any
from agents import function_tool


@function_tool
def print_working_directory_tool() -> Dict[str, Any]:
    """
    Return the current working directory.
    
    Returns:
        A dictionary with the current working directory or an error message.
    """
    print("Printing working directory")
    try:
        return {"path": os.getcwd(), "error": None}
    except Exception as e:
        return {"error": str(e), "path": None}
