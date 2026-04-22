def fix_arg(subdirectory: str, arg: str) -> str:
    arg_path = Path(arg)
    if not (arg_path.exists() and is_relative_to(arg_path, subdirectory)):
        return arg
    return str(arg_path.relative_to(subdirectory))