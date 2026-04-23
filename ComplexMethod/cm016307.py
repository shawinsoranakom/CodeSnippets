def get_shim_functions(
    shim_files: list[Path | str] | None = None,
) -> dict[str, tuple[int, int]]:
    """
    Extract function names from shim header files and their required version.
    Returns a dict mapping function name to (major, minor) version tuple.

    Only functions defined inside TORCH_FEATURE_VERSION blocks are extracted.
    Functions without version guards are ignored.

    Args:
        shim_files: List of paths to shim header files. If None, will use the default
                    paths to torch/csrc/stable/c/shim.h and
                    torch/csrc/inductor/aoti_torch/c/shim.h based on the repository root.
    """
    if shim_files is None:
        repo_root = Path(__file__).resolve().parents[3]
        shim_files_to_check = [
            repo_root / "torch/csrc/stable/c/shim.h",
            repo_root / "torch/csrc/inductor/aoti_torch/c/shim.h",
        ]
    else:
        shim_files_to_check = [Path(f) for f in shim_files]

    # Assert that all shim files exist
    missing_files = [f for f in shim_files_to_check if not f.exists()]
    if missing_files:
        raise RuntimeError(
            f"The following shim files do not exist: {missing_files}. "
            "Ensure all shim header files exist in the repository."
        )

    functions: dict[str, tuple[int, int]] = {}

    # Match function declarations like: AOTI_TORCH_EXPORT ... function_name(
    function_pattern = re.compile(r"AOTI_TORCH_EXPORT.+?(\w+)\s*\(")
    # Also match typedef function pointers
    typedef_pattern = re.compile(r"typedef\s+.*\(\*(\w+)\)")
    # Match using declarations like: using TypeName = ...
    using_pattern = re.compile(r"using\s+(\w+)\s*=")
    # Match struct/class declarations like: struct StructName or class ClassName
    struct_class_pattern = re.compile(r"(?:struct|class)\s+(\w+)")

    for shim_file in shim_files_to_check:
        with open(shim_file) as f:
            lines = f.readlines()

        tracker = PreprocessorTracker()

        for line in lines:
            is_directive_or_comment = tracker.process_line(line)

            # Only look for function declarations if not a comment/directive and inside a version block
            if not is_directive_or_comment:
                version_of_block = tracker.get_version_of_block()
                if version_of_block:
                    stripped = line.strip()
                    func_match = function_pattern.search(stripped)
                    if func_match:
                        func_name = func_match.group(1)
                        functions[func_name] = version_of_block
                        continue

                    typedef_match = typedef_pattern.search(stripped)
                    if typedef_match:
                        func_name = typedef_match.group(1)
                        functions[func_name] = version_of_block
                        continue

                    using_match = using_pattern.search(stripped)
                    if using_match:
                        type_name = using_match.group(1)
                        functions[type_name] = version_of_block
                        continue

                    struct_class_match = struct_class_pattern.search(stripped)
                    if struct_class_match:
                        type_name = struct_class_match.group(1)
                        functions[type_name] = version_of_block
                        continue

    if not functions:
        raise RuntimeError(
            "Could not find any versioned shim functions. "
            "Ensure at least one of the shim files exists and contains versioned functions."
        )

    return functions