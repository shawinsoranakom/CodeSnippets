def _fix_sys_argv(main_script_path: str, args: List[str]) -> None:
    """sys.argv needs to exclude streamlit arguments and parameters
    and be set to what a user's script may expect.
    """
    import sys

    sys.argv = [main_script_path] + list(args)