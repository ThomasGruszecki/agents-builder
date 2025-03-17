from agents import function_tool

@function_tool
def semantic_patch_file_tool(path: str, patch_operations: str) -> str:
    """
    Apply a semantic patch to a file using a unified diff-like format that's easier for LLMs to generate.

    Args:
        path: The file path to edit
        patch_operations: A string containing patch operations in the following format:
            ```
            @@ Context line before change (for matching) @@
            - Line to remove
            + Line to add
            @@ Another context marker @@
            - Another line to remove
            - Second line to remove
            + Replacement line
            ```

    Returns:
        A message indicating success or error
    """
    print(f"Applying semantic patch to file: {path}")

    try:
        # Read the original file
        try:
            with open(path, "r") as f:
                original_content = f.read()
                original_lines = original_content.splitlines()
        except FileNotFoundError:
            return f"Error: File '{path}' not found"

        # Parse the patch operations
        patch_lines = patch_operations.strip().splitlines()
        edited_content = original_content

        # Process each patch section
        i = 0
        while i < len(patch_lines):
            line = patch_lines[i].strip()

            # Find context markers
            if line.startswith("@@") and line.endswith("@@"):
                context = line[2:-2].strip()
                if context not in edited_content:
                    return f"Error: Context '{context}' not found in file"

                # Collect remove and add lines
                remove_lines = []
                add_lines = []
                j = i + 1

                while j < len(patch_lines) and not patch_lines[j].strip().startswith(
                    "@@"
                ):
                    pline = patch_lines[j].strip()
                    if pline.startswith("-"):
                        remove_lines.append(pline[1:].strip())
                    elif pline.startswith("+"):
                        add_lines.append(pline[1:].strip())
                    j += 1

                # Apply the changes
                if remove_lines:
                    remove_block = "\n".join(remove_lines)
                    if remove_block not in edited_content:
                        return (
                            f"Error: Block to remove not found near context '{context}'"
                        )

                    add_block = "\n".join(add_lines) if add_lines else ""
                    edited_content = edited_content.replace(remove_block, add_block)
                else:
                    # Just insertion, no removal
                    context_pos = edited_content.find(context) + len(context)
                    add_block = "\n".join(add_lines)
                    edited_content = (
                        edited_content[:context_pos]
                        + "\n"
                        + add_block
                        + edited_content[context_pos:]
                    )

                i = j
            else:
                i += 1

        # Write the edited content back to the file
        with open(path, "w") as f:
            f.write(edited_content)

        return f"Successfully applied semantic patch to file: {path}"
    except Exception as e:
        print(f"Error applying semantic patch: {str(e)}")
        return f"Error applying semantic patch: {str(e)}"
