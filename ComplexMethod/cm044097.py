def find_decorator(file_path: str, function_name: str) -> str:
    """Find the @router.command decorator of the function in the file, supporting multiline decorators."""
    this_dir = os.path.dirname(os.path.abspath(__file__))
    normalized_dir = this_dir.replace("\\", "/")
    base_path = normalized_dir.split("openbb_platform/")[0]
    file_path = os.path.join(base_path, "openbb_platform", file_path)

    with open(file_path) as file:
        lines = file.readlines()

    decorator_lines = []
    capturing_decorator = False
    for line in lines:
        stripped_line = line.strip()
        # Start capturing lines if we encounter a decorator
        if stripped_line.startswith("@router.command"):
            capturing_decorator = True
            decorator_lines.append(stripped_line)
        elif capturing_decorator:
            # If we're currently capturing a decorator and the line is part of it (indentation or open parenthesis)
            if (
                stripped_line.startswith("@")
                or "def" in stripped_line
                and function_name in stripped_line
            ):
                # If we've reached another decorator or the function definition, stop capturing
                capturing_decorator = False
                # If it's the target function, break, else clear decorator_lines for the next decorator
                if "def" in stripped_line and function_name in stripped_line:
                    break
                decorator_lines = []
            else:
                # It's part of the multiline decorator
                decorator_lines.append(stripped_line)

    decorator = " ".join(decorator_lines)
    return decorator