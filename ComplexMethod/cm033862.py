def _find_module(self, name_parts):
        # synthesize empty inits for packages down through module_utils- we don't want to allow those to be shipped over, but the
        # package hierarchy needs to exist
        if len(name_parts) < 6:
            self.source_code = b''
            self.is_package = True
            return True

        # NB: we can't use pkgutil.get_data safely here, since we don't want to import/execute package/module code on
        # the controller while analyzing/assembling the module, so we'll have to manually import the collection's
        # Python package to locate it (import root collection, reassemble resource path beneath, fetch source)

        collection_pkg_name = '.'.join(name_parts[0:3])
        resource_base_path = os.path.join(*name_parts[3:])

        src = None

        # look for package_dir first, then module
        src_path = to_native(os.path.join(resource_base_path, '__init__.py'))

        try:
            collection_pkg = importlib.import_module(collection_pkg_name)
            pkg_path = os.path.dirname(collection_pkg.__file__)
        except (ImportError, AttributeError):
            pkg_path = None

        try:
            src = pkgutil.get_data(collection_pkg_name, src_path)
        except ImportError:
            pass

        # TODO: we might want to synthesize fake inits for py3-style packages, for now they're required beneath module_utils

        if src is not None:  # empty string is OK
            self.is_package = True
        else:
            src_path = to_native(resource_base_path + '.py')

            try:
                src = pkgutil.get_data(collection_pkg_name, src_path)
            except ImportError:
                pass

        if src is None:  # empty string is OK
            return False

        # TODO: this feels brittle and funky; we should be able to more definitively assure the source path

        if pkg_path:
            origin = Origin(path=os.path.join(pkg_path, src_path))
        else:
            # DTFIX-FUTURE: not sure if this case is even reachable
            origin = Origin(description=f'<synthetic collection package for {collection_pkg_name}!r>')

        self.source_code = origin.tag(src)
        return True