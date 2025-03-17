import os
from typing import List, Dict, Any
from agents import function_tool


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
    print(f"Creating directory: {path}")
    try:
        os.makedirs(path, exist_ok=True)
        return {"success": True, "error": None}
    except Exception as e:
        return {"success": False, "error": str(e)}
