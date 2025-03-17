import subprocess as sp
from typing import Dict, Any
from agents import function_tool


@function_tool
def run_command_tool(command: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Run a shell command and return the result.

    Args:
        command: The command to run.
        timeout: Maximum time in seconds to wait for the command to complete.

    Returns:
        A dictionary with stdout, stderr, and return code.
    """
    print(f"Running command: {command}")
    try:
        result = sp.run(
            command, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "error": None,
        }
    except sp.TimeoutExpired:
        return {"error": f"Command timed out after {timeout} seconds"}
    except Exception as e:
        return {"error": str(e)}
