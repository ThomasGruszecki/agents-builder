import os
from typing import List, Dict, Any
from agents import function_tool

# Project structure and code management tools
@function_tool
def create_directory_tool(path: str) -> Dict[str, Any]:
    """
    Create a new directory at the specified path. If the directory already exists, 
    this tool will not raise an error (exist_ok=True is used).

    Args:
        path: The directory path to create. Can be a relative or absolute path.
             For nested directories, all intermediate directories will also be created.

    Returns:
        A dictionary with the following keys:
            - success: Boolean indicating whether the operation succeeded
            - error: None if successful, otherwise contains the error message as a string
    
    Examples:
        # Create a directory named 'data' in the current working directory
        create_directory_tool("data")
        
        # Create a nested directory structure
        create_directory_tool("project/src/modules")
    """
    print(f"Creating directory: {path}")
    try:
        os.makedirs(path, exist_ok=True)
        return {"success": True, "error": None}
    except Exception as e:
        return {"success": False, "error": str(e)}
