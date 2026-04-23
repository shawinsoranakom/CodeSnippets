async def _find_tool(
    tool: str,
    llvm_version: str,
    llvm_tools_install_dir: str | None,
    *,
    echo: bool = False,
) -> str | None:
    # Explicitly defined LLVM installation location
    if llvm_tools_install_dir:
        path = os.path.join(llvm_tools_install_dir, "bin", tool)
        if await _check_tool_version(path, llvm_version, echo=echo):
            return path
    # Unversioned executables:
    path = tool
    if await _check_tool_version(path, llvm_version, echo=echo):
        return path
    # Versioned executables:
    path = f"{tool}-{llvm_version}"
    if await _check_tool_version(path, llvm_version, echo=echo):
        return path
    # PCbuild externals:
    externals = os.environ.get("EXTERNALS_DIR", _targets.EXTERNALS)
    path = os.path.join(externals, _EXTERNALS_LLVM_TAG, "bin", tool)
    # On Windows, executables need .exe extension
    if os.name == "nt" and not path.endswith(".exe"):
        path_with_exe = path + ".exe"
        if os.path.exists(path_with_exe):
            path = path_with_exe
    if await _check_tool_version(path, llvm_version, echo=echo):
        return path
    # Homebrew-installed executables:
    prefix = await _get_brew_llvm_prefix(llvm_version, echo=echo)
    if prefix is not None:
        path = os.path.join(prefix, "bin", tool)
        if await _check_tool_version(path, llvm_version, echo=echo):
            return path
    # Nothing found:
    return None