import os
from typing import Dict, Any
from agents import function_tool


@function_tool
def search_files_tool(
    pattern: str, path: str = ".", recursive: bool = True
) -> Dict[str, Any]:
    """
    Search for files matching a pattern.

    Args:
        pattern: The pattern to search for (supports glob syntax).
        path: The directory to search in.
        recursive: Whether to search recursively.

    Returns:
        A dictionary with matching files.
    """
    print(f"Searching files: {pattern} in {path}")
    try:
        import glob

        search_pattern = (
            os.path.join(path, "**", pattern)
            if recursive
            else os.path.join(path, pattern)
        )
        matches = glob.glob(search_pattern, recursive=recursive)

        return {"matches": matches, "count": len(matches), "error": None}
    except Exception as e:
        return {"error": str(e), "matches": []}
