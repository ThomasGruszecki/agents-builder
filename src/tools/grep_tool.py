from typing import Dict, Any
from agents import function_tool


@function_tool
def grep_tool(pattern: str, file_path: str) -> Dict[str, Any]:
    """
    Search for a pattern in a file.

    Args:
        pattern: The pattern to search for.
        file_path: The file to search in.

    Returns:
        A dictionary with matching lines.
    """
    print(f"Searching for pattern: {pattern} in file: {file_path}")
    try:
        import re

        matches = []

        with open(file_path, "r") as f:
            for i, line in enumerate(f, 1):
                if re.search(pattern, line):
                    matches.append({"line_number": i, "content": line.rstrip()})

        return {"matches": matches, "count": len(matches), "error": None}
    except FileNotFoundError:
        return {"error": f"File '{file_path}' not found", "matches": []}
    except Exception as e:
        return {"error": str(e), "matches": []}
