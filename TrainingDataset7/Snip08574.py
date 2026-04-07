def validate_file_name(name, allow_relative_path=False):
    # Remove potentially dangerous names
    if os.path.basename(name) in {"", ".", ".."}:
        raise SuspiciousFileOperation("Could not derive file name from '%s'" % name)

    if allow_relative_path:
        # Ensure that name can be treated as a pure posix path, i.e. Unix
        # style (with forward slashes).
        path = pathlib.PurePosixPath(str(name).replace("\\", "/"))
        if path.is_absolute() or ".." in path.parts:
            raise SuspiciousFileOperation(
                "Detected path traversal attempt in '%s'" % name
            )
    elif name != os.path.basename(name):
        raise SuspiciousFileOperation("File name '%s' includes path elements" % name)

    return name