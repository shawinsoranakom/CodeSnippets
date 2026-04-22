def _get_filenames(dir):
    dir = os.path.abspath(dir)
    return [
        os.path.join(dir, filename)
        for filename in sorted(os.listdir(dir))
        if filename.endswith(".py") and filename not in EXCLUDED_FILENAMES
    ]