def check_code_blocks(markdown_file_paths: List[str]) -> None:
    """Check Python code blocks in a Markdown file for syntax errors."""
    files_with_errors = []

    for markdown_file_path in markdown_file_paths:
        code_blocks = extract_python_code_blocks(markdown_file_path)
        had_errors = False
        for code_block, line_no in code_blocks:
            markdown_file_path_with_line_no = f"{markdown_file_path}:{line_no}"
            logger.info("Checking a code block in %s...", markdown_file_path_with_line_no)

            # Skip blocks that don't import autogen_agentchat, autogen_core, or autogen_ext
            if all(all(import_code not in code_block for import_code in [f"import {module}", f"from {module}"]) for module in ["autogen_agentchat", "autogen_core", "autogen_ext"]):
                logger.info(" " + darkgreen("OK[ignored]"))
                continue

            with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
                temp_file.write(code_block.encode("utf-8"))
                temp_file.flush()

                # Run pyright on the temporary file using subprocess.run
                import subprocess

                result = subprocess.run(["pyright", temp_file.name], capture_output=True, text=True)
                if result.returncode != 0:
                    logger.info(" " + darkred("FAIL"))
                    highlighted_code = highlight(code_block, PythonLexer(), TerminalFormatter())  # type: ignore
                    output = f"{faint('========================================================')}\n{red('Error')}: Pyright found issues in {teal(markdown_file_path_with_line_no)}:\n{faint('--------------------------------------------------------')}\n{highlighted_code}\n{faint('--------------------------------------------------------')}\n\n{teal('pyright output:')}\n{red(result.stdout)}{faint('========================================================')}\n"
                    logger.info(output)
                    had_errors = True
                else:
                    logger.info(" " + darkgreen("OK"))

        if had_errors:
            files_with_errors.append(markdown_file_path)

    if files_with_errors:
        raise RuntimeError("Syntax errors found in the following files:\n" + "\n".join(files_with_errors))