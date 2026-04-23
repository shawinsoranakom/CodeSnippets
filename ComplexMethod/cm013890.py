def check_file(filename: str | None, is_inlined_call: bool = False) -> SkipResult:
    """Should skip this file?"""
    if filename is None:
        return SkipResult(
            True, "cannot determine source file (likely a C extension or builtin)"
        )
    filename = _as_posix_path(filename)
    if filename in FORCE_SKIP_FILES:
        return SkipResult(True, f"file is force-skipped ({filename})")

    for d in get_legacy_mod_inlinelist():
        if filename.startswith(d):
            return SkipResult(False, f"file matches LEGACY_MOD_INLINELIST ({d})")
    if is_inlined_call and is_torch_inline_allowed(filename):
        return SkipResult(False, f"file matches MOD_INLINELIST ({filename})")
    if is_inlined_call and any(
        filename.startswith(d) for d in BUILTIN_INLINE_WHEN_CALLED
    ):
        return SkipResult(
            False, f"file matches BUILTIN_INLINE_WHEN_CALLED ({filename})"
        )
    if (
        is_fbcode()
        and FBCODE_SKIP_DIRS
        and bool(FBCODE_SKIP_DIRS_RE.match(filename))
        and not bool(FBCODE_INLINE_FILES_IN_SKIPPED_DIRS_RE.match(filename))
    ):
        return SkipResult(True, "file matches FBCODE_SKIP_DIRS")

    if (
        is_fbcode()
        and config.skip_torchrec
        and FBCODE_SKIP_TORCHREC_DIRS
        and bool(FBCODE_SKIP_TORCHREC_DIRS_RE.match(filename))
        and not bool(FBCODE_INLINE_FILES_IN_SKIPPED_DIRS_RE.match(filename))
    ):
        return SkipResult(True, "file matches FBCODE_SKIP_TORCHREC_DIRS")

    unittest_dir = _module_dir(unittest)
    if (
        unittest_dir is not None
        and filename.startswith(unittest_dir)
        and not torch._dynamo.config.enable_trace_unittest
    ):
        return SkipResult(True, "file is in unittest directory")

    if bool(SKIP_DIRS_RE.match(filename)):
        matched_dir = next((d for d in SKIP_DIRS if filename.startswith(d)), filename)
        return SkipResult(True, f"file is under skip directory ({matched_dir})")

    for d in get_mod_skiplist():
        if filename.startswith(d):
            return SkipResult(True, f"file matches MOD_SKIPLIST ({d})")
    return SkipResult(False, "inlined by default")