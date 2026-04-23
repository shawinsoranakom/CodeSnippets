def remove_if_exists(path):
    """Remove the given folder or file if it exists"""
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)