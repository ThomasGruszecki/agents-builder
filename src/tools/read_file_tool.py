import os
from typing import Dict, Any
from agents import function_tool


@function_tool
def read_file_tool(path: str) -> Dict[str, Any]:
    """
    Read and return the contents of the given file.

    Args:
        path: The path to the file to read.

    Returns:
        A dictionary with the file content or an error message.
    """
    print(f"Reading file: {path}")
    try:
        with open(path, "r") as f:
            content = f.read()

        # Add file metadata
        file_size = os.path.getsize(path)
        file_extension = os.path.splitext(path)[1]

        return {
            "content": content,
            "size": file_size,
            "extension": file_extension,
            "error": None,
        }
    except FileNotFoundError:
        return {"error": f"File '{path}' not found", "content": None}
    except Exception as e:
        return {"error": str(e), "content": None}
