def get_checker_command(name, fix=False):
    """Return a shell-friendly command string for a checker."""
    if name == "deps_table":
        return "python setup.py deps_table_update"
    if name == "imports":
        return 'python -c "from transformers import *"'
    if name == "ruff_check":
        cmd = ["ruff", "check", *RUFF_TARGETS]
        if fix:
            cmd += ["--fix", "--exclude", ""]
        return " ".join(cmd)
    if name == "ruff_format":
        cmd = ["ruff", "format", *RUFF_TARGETS]
        if not fix:
            cmd += ["--check"]
        else:
            cmd += ["--exclude", ""]
        return " ".join(cmd)

    _, script, check_args, fix_args = CHECKERS[name]
    if fix and fix_args is None:
        return None
    args = fix_args if fix else check_args
    return " ".join(["python", f"utils/{script}"] + args)