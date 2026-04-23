def _get_spec(cls, fullname, path, target=None):
        """Find the loader or namespace_path for this module/package name."""
        # If this ends up being a namespace package, namespace_path is
        #  the list of paths that will become its __path__
        namespace_path = []
        for entry in path:
            if not isinstance(entry, str):
                continue
            finder = cls._path_importer_cache(entry)
            if finder is not None:
                spec = finder.find_spec(fullname, target)
                if spec is None:
                    continue
                if spec.loader is not None:
                    return spec
                portions = spec.submodule_search_locations
                if portions is None:
                    raise ImportError('spec missing loader')
                # This is possibly part of a namespace package.
                #  Remember these path entries (if any) for when we
                #  create a namespace package, and continue iterating
                #  on path.
                namespace_path.extend(portions)
        else:
            spec = _bootstrap.ModuleSpec(fullname, None)
            spec.submodule_search_locations = namespace_path
            return spec