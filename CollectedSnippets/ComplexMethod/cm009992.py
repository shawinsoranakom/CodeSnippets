def copy_libraries(torch_dir: Path, libtorch_lib: Path, platform: str) -> None:
    """Copy libraries from torch/lib/ to libtorch/lib/."""
    torch_lib = torch_dir / "lib"
    if not torch_lib.is_dir():
        raise FileNotFoundError(f"torch/lib/ not found at {torch_lib}")

    for item in torch_lib.iterdir():
        if item.is_dir():
            # Copy subdirectories (e.g. libshm/) as-is
            shutil.copytree(item, libtorch_lib / item.name, dirs_exist_ok=True)
            continue
        if should_exclude_lib(item.name):
            continue
        if _is_lib_file(item.name, platform):
            shutil.copy2(item, libtorch_lib / item.name)

    # On macOS, also copy delocated dylibs from torch/.dylibs/ if present
    if platform == "macos":
        dylibs_dir = torch_dir / ".dylibs"
        if dylibs_dir.is_dir():
            for item in dylibs_dir.iterdir():
                if item.suffix == ".dylib" and not should_exclude_lib(item.name):
                    shutil.copy2(item, libtorch_lib / item.name)