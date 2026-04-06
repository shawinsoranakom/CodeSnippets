def get_installation_version():
    try:
        from importlib.metadata import version

        return version('thefuck')
    except ImportError:
        import pkg_resources

        return pkg_resources.require('thefuck')[0].version