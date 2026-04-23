def get_locator(file):
    file_contents = file.read_text(encoding="utf-8")
    return CodeLocator.from_code(file_contents)