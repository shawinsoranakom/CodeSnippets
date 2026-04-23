def _init_callback_methods(self) -> None:
        """Record analysis of callback methods on each callback instance for dispatch optimization and deprecation warnings."""
        implemented_callback_methods: set[str] = set()
        deprecated_v1_method_overrides: set[str] = set()
        plugin_file = sys.modules[type(self).__module__].__file__

        if plugin_info := _deprecator._path_as_plugininfo(plugin_file):
            plugin_name = plugin_info.resolved_name
        else:
            plugin_name = plugin_file

        for base_v2_method, base_v1_method in CallbackBase._v2_v1_method_map.items():
            method_name = None

            if not inspect.ismethod(method := getattr(self, (v2_method_name := base_v2_method.__name__))) or method.__func__ is not base_v2_method:
                implemented_callback_methods.add(v2_method_name)  # v2 method directly implemented by subclass
                method_name = v2_method_name
            elif base_v1_method is None:
                pass  # no corresponding v1 method
            elif not inspect.ismethod(method := getattr(self, (v1_method_name := base_v1_method.__name__))) or method.__func__ is not base_v1_method:
                implemented_callback_methods.add(v2_method_name)  # v1 method directly implemented by subclass
                deprecated_v1_method_overrides.add(v1_method_name)
                method_name = v1_method_name

            if method_name and v2_method_name == 'v2_on_any':
                deprecated_v1_method_overrides.discard(method_name)  # avoid including v1 on_any in the v1 deprecation below

                global_display.deprecated(
                    msg=f'The {plugin_name!r} callback plugin implements deprecated method {method_name!r}.',
                    version='2.23',
                    help_text='Use event-specific callback methods instead.',
                )

        self._implemented_callback_methods = frozenset(implemented_callback_methods)

        if deprecated_v1_method_overrides:
            global_display.deprecated(
                msg=f'The {plugin_name!r} callback plugin implements the following deprecated method(s): {", ".join(sorted(deprecated_v1_method_overrides))}',
                version='2.23',
                help_text='Implement the `v2_*` equivalent callback method(s) instead.',
            )