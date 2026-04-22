def _make_it_absolute(path):
        # Use manual join instead of os.abspath to test against non normalized paths
        return os.path.join(os.getcwd(), path)