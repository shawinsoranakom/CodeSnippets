def parse_diff_ranges(diff: str) -> dict[str, "ChangedFile"]:
    """Parse a unified diff and extract changed line ranges per file."""
    files = {}
    current_file = None
    pending_rename_from = None
    is_rename = False

    for line in diff.split("\n"):
        # Reset rename state on new file diff header
        if line.startswith("diff --git "):
            is_rename = False
            pending_rename_from = None
        elif line.startswith("rename from "):
            pending_rename_from = line[12:]
            is_rename = True
        elif line.startswith("rename to "):
            pass  # rename target is captured via "+++ b/" line
        elif line.startswith("similarity index"):
            is_rename = True
        elif line.startswith("+++ b/"):
            path = line[6:]
            current_file = ChangedFile(
                path=path,
                additions=[],
                deletions=[],
                is_rename=is_rename,
                old_path=pending_rename_from
            )
            files[path] = current_file
            pending_rename_from = None
            is_rename = False
        elif line.startswith("--- /dev/null"):
            is_rename = False
            pending_rename_from = None
        elif line.startswith("@@") and current_file:
            parse_hunk_header(line, current_file)

    return files