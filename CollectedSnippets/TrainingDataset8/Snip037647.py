def is_executable_in_path(name):
    """Check if executable is in OS path."""
    from distutils.spawn import find_executable

    return find_executable(name) is not None