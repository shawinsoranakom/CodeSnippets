def ok_changed_file(file: str) -> bool:
    # Return true if the file is in the list of allowed files to be changed to
    # reuse the old whl
    if (
        file.startswith("torch/")
        and file.endswith(".py")
        and not file.startswith("torch/csrc/")
    ):
        return True
    if file.startswith("test/") and file.endswith(".py"):
        return True
    if file.startswith("docs/") and file.endswith((".md", ".rst")):
        return True
    return False