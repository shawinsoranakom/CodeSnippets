def _get_source(self, filename, loader, module_name):
        source = None
        if hasattr(loader, "get_source"):
            try:
                source = loader.get_source(module_name)
            except ImportError:
                pass
            if source is not None:
                source = source.splitlines()
        if source is None:
            try:
                with open(filename, "rb") as fp:
                    source = fp.read().splitlines()
            except OSError:
                pass
        return source