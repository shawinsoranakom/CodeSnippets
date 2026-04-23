def is_dir_writable(path):
    try:
        with tempfile.NamedTemporaryFile(dir=path):
            pass
    except OSError:
        return False
    return True