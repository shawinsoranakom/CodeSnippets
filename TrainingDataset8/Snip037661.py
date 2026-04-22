def get_assets_dir():
    """Get the folder where static assets live."""
    dirname = os.path.dirname(os.path.normpath(__file__))
    return os.path.normpath(os.path.join(dirname, "static/assets"))