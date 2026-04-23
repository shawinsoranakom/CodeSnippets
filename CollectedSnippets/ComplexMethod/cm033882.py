def all(self, *args, **kwargs):
        kwargs.pop('_dedupe', None)
        path_only = kwargs.pop('path_only', False)
        class_only = kwargs.pop('class_only', False)  # basically ignored for test/filters since they are functions

        # Having both path_only and class_only is a coding bug
        if path_only and class_only:
            raise AnsibleError('Do not set both path_only and class_only when calling PluginLoader.all()')

        self._ensure_non_collection_wrappers(*args, **kwargs)

        plugins = [plugin for plugin in self._cached_non_collection_wrappers.values() if not isinstance(plugin, _DeferredPluginLoadFailure)]

        if path_only:
            yield from (w._original_path for w in plugins)
        else:
            yield from (w for w in plugins)