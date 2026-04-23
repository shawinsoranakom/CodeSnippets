def get_static_dir():
    """Get the folder where static HTML/JS/CSS files live."""
    dirname = os.path.dirname(os.path.normpath(__file__))
    return os.path.normpath(os.path.join(dirname, "static"))