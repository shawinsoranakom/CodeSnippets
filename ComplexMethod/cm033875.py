def _query_collection_routing_meta(self, acr, plugin_type, extension=None):
        try:
            if not (collection_pkg := import_module(acr.n_python_collection_package_name)):
                return None
        except ImportError:
            return None

        # FIXME: shouldn't need this...
        try:
            # force any type-specific metadata postprocessing to occur
            import_module(acr.n_python_collection_package_name + '.plugins.{0}'.format(plugin_type))
        except ImportError:
            pass

        # this will be created by the collection PEP302 loader
        collection_meta = getattr(collection_pkg, '_collection_meta', None)

        if not collection_meta:
            return None

        # TODO: add subdirs support
        # check for extension-specific entry first (eg 'setup.ps1')
        # TODO: str/bytes on extension/name munging
        if acr.subdirs:
            subdir_qualified_resource = '.'.join([acr.subdirs, acr.resource])
        else:
            subdir_qualified_resource = acr.resource
        entry = collection_meta.get('plugin_routing', {}).get(plugin_type, {}).get(subdir_qualified_resource + (extension or ''), None)
        if not entry:
            # try for extension-agnostic entry
            entry = collection_meta.get('plugin_routing', {}).get(plugin_type, {}).get(subdir_qualified_resource, None)
        return entry