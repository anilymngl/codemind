import os
from pathlib import Path
from typing import Union

EXCLUDED_DIRS = {'node_modules', '.git',"backup-old-codes","codemind_mvp.egg-info",
                 'mvp_orchestrator/__pycache__','__pycache__','venv','env','docs'}

def print_directory_structure(start_path: Union[str, Path]) -> None:
    """
    Prints the directory structure starting from the given path and saves it to a Markdown file.
    Also includes a list of full paths in a separate Markdown file.

    Args:
        start_path (str | Path): The root directory path to start printing from.

    Raises:
        ValueError: If the start_path does not exist or is not a directory.
        IOError: If there is an error writing to the Markdown files.
    """
    start_path = Path(start_path)

    if not start_path.exists():
        raise ValueError(f"The path {start_path} does not exist.")
    if not start_path.is_dir():
        raise ValueError(f"The path {start_path} is not a directory.")

    directory_tree_file = start_path / "project_structure.md"
    full_paths_file = start_path / "project_structure_full_paths.md"

    try:
        with open(directory_tree_file, "w", encoding="utf-8") as md_tree, \
             open(full_paths_file, "w", encoding="utf-8") as md_paths:
            md_tree.write(f"# Project Structure for {start_path.resolve()}\n\n")
            md_tree.write("## Directory Tree\n\n")
            for root, dirs, files in os.walk(start_path):
                # Exclude specified directories
                dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

                root_path = Path(root)
                relative_path = root_path.relative_to(start_path)
                level = len(relative_path.parts)
                indent = ' ' * 4 * level
                md_tree.write(f"{indent}- **{root_path.name}/**\n")
                sub_indent = ' ' * 4 * (level + 1)
                for file in files:
                    md_tree.write(f"{sub_indent}- {file}\n")

            md_paths.write(f"# Full Paths for {start_path.resolve()}\n\n")
            md_paths.write("Note: The paths below are relative to the root directory.\n\n")
            for root, dirs, files in os.walk(start_path):
                dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
                for file in files:
                    file_path = Path(root) / file
                    relative_file_path = file_path.relative_to(start_path)
                    md_paths.write(f"- {str(relative_file_path)}\n")

        print(f"Project structure saved to {directory_tree_file.resolve()}")
        print(f"Full paths saved to {full_paths_file.resolve()}")
    except IOError as e:
        raise IOError(f"An error occurred while writing to the Markdown files: {e}")

# Replace 'your_directory_path' with the path you want to start from
start_path = Path(r'C:\Users\AnilYamangil\OneDrive - BlueCloud Services, Inc\Desktop\codemind')
print_directory_structure(start_path)
