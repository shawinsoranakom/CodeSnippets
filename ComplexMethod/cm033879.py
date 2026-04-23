def get_with_context(self, name, *args, **kwargs) -> get_with_context_result:
        """ instantiates a plugin of the given name using arguments """

        if not name:
            raise ValueError('A non-empty plugin name is required.')

        found_in_cache = True
        class_only = kwargs.pop('class_only', False)
        collection_list = kwargs.pop('collection_list', None)
        if name in self._aliases:
            name = self._aliases[name]

        if (cached_result := (self._plugin_instance_cache or {}).get(name)) and cached_result[1].resolved:
            # Resolving the FQCN is slow, even if we've passed in the resolved FQCN.
            # Short-circuit here if we've previously resolved this name.
            # This will need to be restricted if non-vars plugins start using the cache, since
            # some non-fqcn plugin need to be resolved again with the collections list.
            return get_with_context_result(*cached_result)

        plugin_load_context = self.find_plugin_with_context(name, collection_list=collection_list)
        if not plugin_load_context.resolved or not plugin_load_context.plugin_resolved_path:
            # FIXME: this is probably an error (eg removed plugin)
            return get_with_context_result(None, plugin_load_context)

        fq_name = plugin_load_context.resolved_fqcn
        resolved_type_name = plugin_load_context.plugin_resolved_name
        path = plugin_load_context.plugin_resolved_path
        if (cached_result := (self._plugin_instance_cache or {}).get(fq_name)) and cached_result[1].resolved:
            # This is unused by vars plugins, but it's here in case the instance cache expands to other plugin types.
            # We get here if we've seen this plugin before, but it wasn't called with the resolved FQCN.
            return get_with_context_result(*cached_result)
        redirected_names = plugin_load_context.redirect_list or []

        if path not in self._module_cache:
            self._module_cache[path] = self._load_module_source(python_module_name=plugin_load_context._python_module_name, path=path)
            found_in_cache = False

        self._load_config_defs(resolved_type_name, self._module_cache[path], path)

        obj = getattr(self._module_cache[path], self.class_name)

        if self.base_class:
            # The import path is hardcoded and should be the right place,
            # so we are not expecting an ImportError.
            module = __import__(self.package, fromlist=[self.base_class])
            # Check whether this obj has the required base class.
            try:
                plugin_class = getattr(module, self.base_class)
            except AttributeError:
                return get_with_context_result(None, plugin_load_context)
            if not issubclass(obj, plugin_class):
                display.warning(f"Ignoring {self.type} plugin {resolved_type_name!r} due to missing base class {self.base_class!r}.")
                return get_with_context_result(None, plugin_load_context)

        # FIXME: update this to use the load context
        self._display_plugin_load(self.class_name, resolved_type_name, self._searched_paths, path, found_in_cache=found_in_cache, class_only=class_only)

        if not class_only:
            try:
                # A plugin may need to use its _load_name in __init__ (for example, to set
                # or get options from config), so update the object before using the constructor
                instance = object.__new__(obj)
                self._update_object(obj=instance, name=resolved_type_name, path=path, redirected_names=redirected_names, resolved=fq_name)
                obj.__init__(instance, *args, **kwargs)  # pylint: disable=unnecessary-dunder-call
                obj = instance
            except TypeError as e:
                if "abstract" in e.args[0]:
                    # Abstract Base Class or incomplete plugin, don't load
                    display.v('Returning not found on "%s" as it has unimplemented abstract methods; %s' % (resolved_type_name, to_native(e)))
                    return get_with_context_result(None, plugin_load_context)
                raise

        self._update_object(obj=obj, name=resolved_type_name, path=path, redirected_names=redirected_names, resolved=fq_name)
        if self._plugin_instance_cache is not None and getattr(obj, 'is_stateless', False):
            self._plugin_instance_cache[fq_name] = (obj, plugin_load_context)
        elif self._plugin_instance_cache is not None:
            # The cache doubles as the load order, so record the FQCN even if the plugin hasn't set is_stateless = True
            self._plugin_instance_cache[fq_name] = (None, PluginLoadContext(self.type, self.package))
        return get_with_context_result(obj, plugin_load_context)