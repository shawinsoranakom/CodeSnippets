def _get_source_of_module(self, module: types.ModuleType) -> str | None:
        filename = None
        spec = getattr(module, "__spec__", None)
        if spec is not None:
            loader = getattr(spec, "loader", None)
            if loader is not None and isinstance(loader, SourceFileLoader):
                try:
                    filename = loader.get_filename(module.__name__)
                except ImportError:
                    pass
        if filename is None:
            filename = getattr(module, "__file__", None)
        if isinstance(filename, str) and filename.endswith(".py"):
            return "".join(linecache.getlines(filename, module.__dict__))
        return None