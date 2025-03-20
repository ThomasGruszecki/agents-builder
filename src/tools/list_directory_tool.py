import os
from typing import Dict, Any
from agents import function_tool


@function_tool
def list_directory_tool(path: str) -> Dict[str, Any]:
    """
    Return detailed information about files in the given directory.

    Args:
        path: The directory path to list. Defaults to current directory.

    Returns:
        A dictionary with files, directories, and any errors.

    Examples:
        list_directory_tool(".") # Lists the current directory

        list_directory_tool("/home/user/projects") # Lists the projects directory from the home directory
        
        list_directory_tool("src/tools") # Lists the tools directory from the current directory
    
    """
    print(f"Listing directory: {path}")
    try:
        items = os.listdir(path)
        result = {"files": [], "directories": [], "error": None}

        for item in items:
            item_path = os.path.join(path, item)
            try:
                if os.path.isfile(item_path):
                    result["files"].append(
                        {
                            "name": item,
                            "size": os.path.getsize(item_path),
                            "extension": os.path.splitext(item)[1],
                            "modified": os.path.getmtime(item_path),
                        }
                    )
                elif os.path.isdir(item_path):
                    result["directories"].append(item)
            except Exception as e:
                # Skip items with permission issues
                pass

        return result
    except Exception as e:
        return {"error": str(e), "files": [], "directories": []}
