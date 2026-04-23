def lang_to_cmd(lang: str) -> str:
    if lang in PYTHON_VARIANTS:
        return "python"
    if lang.startswith("python") or lang in ["bash", "sh"]:
        return lang
    if lang in ["shell"]:
        return "sh"
    if lang in ["pwsh", "powershell", "ps1"]:
        # Check if pwsh is available, otherwise fall back to powershell
        if shutil.which("pwsh") is not None:
            return "pwsh"
        elif shutil.which("powershell") is not None:
            return "powershell"
        else:
            raise ValueError("Powershell or pwsh is not installed. Please install one of them.")
    else:
        raise ValueError(f"Unsupported language: {lang}")