import os
from agents import function_tool

@function_tool
async def create_file_tool(filename: str, content: str) -> str:
    """
    Creates a new file with the specified filename and content.

    Args:
        filename: The name of the file to create.
        content: The content to write into the file.

    Returns:
        A message indicating the file has been created, or an error message.

    Examples:
        create_file_tool("my_document.txt", "Hello, world!")
        create_file_tool("project/src/main.py", "print('Hello, world!')")
    """

    print(f"Creating file: {filename}")

    try:
        # Ensure the directory exists
        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        with open(filename, "w") as f:
            f.write(content)
        return f"File '{filename}' created successfully."
    except Exception as e:
        return f"Error creating file '{filename}': {e}"