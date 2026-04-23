def full_tex_to_svg(full_tex: str, compiler: str = "latex", message: str = ""):
    if message:
        print(message, end="\r")

    if compiler == "latex":
        dvi_ext = ".dvi"
    elif compiler == "xelatex":
        dvi_ext = ".xdv"
    else:
        raise NotImplementedError(f"Compiler '{compiler}' is not implemented")

    # Use the custom LaTeX cache directory from the config
    temp_dir = Path(manim_config.directories.latex_cache)
    temp_dir.mkdir(exist_ok=True) # Create the directory if it does not already exist

    # Define paths for the intermediate TeX and DVI files
    tex_path = temp_dir / "working.tex"
    dvi_path = tex_path.with_suffix(dvi_ext)

    # Write tex file
    tex_path.write_text(full_tex)

    # Run latex compiler
    process = subprocess.run(
        [
            compiler,
            *(['-no-pdf'] if compiler == "xelatex" else []),
            "-interaction=batchmode",
            "-halt-on-error",
            f"-output-directory={temp_dir}",
            tex_path
        ],
        capture_output=True,
        text=True
    )

    if process.returncode != 0:
        # Handle error
        error_str = ""
        log_path = tex_path.with_suffix(".log")
        if log_path.exists():
            content = log_path.read_text()
            error_match = re.search(r"(?<=\n! ).*\n.*\n", content)
            if error_match:
                error_str = error_match.group()
        raise LatexError(error_str or "LaTeX compilation failed")

    # Run dvisvgm and capture output directly
    process = subprocess.run(
        [
            "dvisvgm",
            dvi_path,
            "-n",  # no fonts
            "-v", "0",  # quiet
            "--stdout",  # output to stdout instead of file
        ],
        capture_output=True
    )

    # Return SVG string
    result = process.stdout.decode('utf-8')

    if message:
        print(" " * len(message), end="\r")

    return result