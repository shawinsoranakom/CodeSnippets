def _get_command_line_as_string() -> Optional[str]:
    import subprocess

    parent = click.get_current_context().parent
    if parent is None:
        return None

    if "streamlit.cli" in parent.command_path:
        raise RuntimeError(
            "Running streamlit via `python -m streamlit.cli <command>` is"
            " unsupported. Please use `python -m streamlit <command>` instead."
        )

    cmd_line_as_list = [parent.command_path]
    cmd_line_as_list.extend(sys.argv[1:])
    return subprocess.list2cmdline(cmd_line_as_list)