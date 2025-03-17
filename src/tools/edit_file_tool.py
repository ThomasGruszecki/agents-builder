import os
from typing import List, Dict, Any
from agents import function_tool


@function_tool
def edit_file_tool(
    path: str, operations: list[dict], read_before_edit: bool = True
) -> str:
    """
    Edit a file with precision using operations instead of rewriting the entire file.

    Args:
        path: The file path to edit
        operations: A list of edit operations, each one being a dict with the following structure:
            - type: The operation type (one of "insert", "delete", "replace", "append")
            - content: The content to insert/replace (for "insert", "replace", "append")
            - target: How to locate the edit position, can be one of:
                - line_number: integer line number (1-indexed)
                - line_range: [start_line, end_line] (1-indexed, inclusive)
                - before_text: string to find (edits before this text)
                - after_text: string to find (edits after this text)
                - replace_text: string to replace
        read_before_edit: Whether to read the file contents before editing (default: True)

    Returns:
        A message indicating success or error

    Examples:
        # Insert a new line after line 5
        edit_file_tool("file.py", [{"type": "insert", "target": {"line_number": 5}, "content": "new_line()"}])

        # Replace text containing a specific string
        edit_file_tool("file.py", [{"type": "replace", "target": {"replace_text": "old_function()"}, "content": "new_function()"}])

        # Delete lines 10-15
        edit_file_tool("file.py", [{"type": "delete", "target": {"line_range": [10, 15]}}])

        # Append to the end of the file
        edit_file_tool("file.py", [{"type": "append", "content": "# End of file"}])
    """
    print(f"Editing file: {path}")

    try:
        # Read original file if needed
        original_content = ""
        if read_before_edit:
            try:
                with open(path, "r") as f:
                    original_content = f.read()
            except FileNotFoundError:
                # File doesn't exist, it's okay for append operations
                if not any(op.get("type") == "append" for op in operations):
                    return f"Error: File '{path}' not found"

        # Split content into lines for line-based operations
        original_lines = original_content.splitlines() if original_content else []
        edited_lines = original_lines.copy()

        # Apply each operation
        for op in operations:
            op_type = op.get("type")
            target = op.get("target", {})
            content = op.get("content", "")

            # Handle append operation (special case)
            if op_type == "append":
                if edited_lines and edited_lines[-1]:
                    edited_lines.append("")  # Ensure newline before append
                edited_lines.append(content)
                continue

            # Find target position for the edit
            if "line_number" in target:
                # Line number targeting (1-indexed)
                line_idx = target["line_number"] - 1
                if line_idx < 0 or line_idx > len(edited_lines):
                    return f"Error: Line number {target['line_number']} out of range"

                if op_type == "insert":
                    edited_lines.insert(line_idx, content)
                elif op_type == "delete":
                    del edited_lines[line_idx]
                elif op_type == "replace":
                    edited_lines[line_idx] = content

            elif "line_range" in target:
                # Line range targeting (1-indexed)
                start_idx, end_idx = (
                    target["line_range"][0] - 1,
                    target["line_range"][1] - 1,
                )
                if start_idx < 0 or end_idx >= len(edited_lines) or start_idx > end_idx:
                    return f"Error: Line range {target['line_range']} out of range"

                if op_type == "delete":
                    del edited_lines[start_idx : end_idx + 1]
                elif op_type == "replace":
                    edited_lines[start_idx : end_idx + 1] = [content]

            elif "before_text" in target:
                # Text-based targeting (before specific text)
                joined_content = "\n".join(edited_lines)
                search_text = target["before_text"]
                if search_text not in joined_content:
                    return f"Error: Text '{search_text}' not found in file"

                pos = joined_content.find(search_text)
                line_count = joined_content[:pos].count("\n")

                if op_type == "insert":
                    edited_lines.insert(line_count, content)

            elif "after_text" in target:
                # Text-based targeting (after specific text)
                joined_content = "\n".join(edited_lines)
                search_text = target["after_text"]
                if search_text not in joined_content:
                    return f"Error: Text '{search_text}' not found in file"

                pos = joined_content.find(search_text) + len(search_text)
                line_count = joined_content[:pos].count("\n")

                if op_type == "insert":
                    edited_lines.insert(line_count + 1, content)

            elif "replace_text" in target:
                # Replace specific text
                joined_content = "\n".join(edited_lines)
                search_text = target["replace_text"]
                if search_text not in joined_content:
                    return f"Error: Text '{search_text}' not found in file"

                if op_type == "replace":
                    joined_content = joined_content.replace(search_text, content)
                    edited_lines = joined_content.splitlines()

        # Write the edited content back to the file
        with open(path, "w") as f:
            f.write("\n".join(edited_lines))
            # Ensure file ends with newline
            if edited_lines:
                f.write("\n")

        return f"Successfully edited file: {path}"
    except Exception as e:
        print(f"Error editing file: {str(e)}")
        return f"Error editing file: {str(e)}"
