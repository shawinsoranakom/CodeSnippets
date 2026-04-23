def all(self, *args, **kwargs):
        """
        Iterate through all plugins of this type, in configured paths (no collections)

        A plugin loader is initialized with a specific type.  This function is an iterator returning
        all of the plugins of that type to the caller.

        :kwarg path_only: If this is set to True, then we return the paths to where the plugins reside
            instead of an instance of the plugin.  This conflicts with class_only and both should
            not be set.
        :kwarg class_only: If this is set to True then we return the python class which implements
            a plugin rather than an instance of the plugin.  This conflicts with path_only and both
            should not be set.
        :kwarg _dedupe: By default, we only return one plugin per plugin name.  Deduplication happens
            in the same way as the :meth:`get` and :meth:`find_plugin` methods resolve which plugin
            should take precedence.  If this is set to False, then we return all of the plugins
            found, including those with duplicate names.  In the case of duplicates, the order in
            which they are returned is the one that would take precedence first, followed by the
            others  in decreasing precedence order.  This should only be used by subclasses which
            want to manage their own deduplication of the plugins.
        :*args: Any extra arguments are passed to each plugin when it is instantiated.
        :**kwargs: Any extra keyword arguments are passed to each plugin when it is instantiated.
        """
        # TODO: Change the signature of this method to:
        # def all(return_type='instance', args=None, kwargs=None):
        #     if args is None: args = []
        #     if kwargs is None: kwargs = {}
        #     return_type can be instance, class, or path.
        #     These changes will mean that plugin parameters won't conflict with our params and
        #     will also make it impossible to request both a path and a class at the same time.
        #
        #     Move _dedupe to be a class attribute, CUSTOM_DEDUPE, with subclasses for filters and
        #     tests setting it to True

        dedupe = kwargs.pop('_dedupe', True)
        path_only = kwargs.pop('path_only', False)
        class_only = kwargs.pop('class_only', False)
        # Having both path_only and class_only is a coding bug
        if path_only and class_only:
            raise AnsibleError('Do not set both path_only and class_only when calling PluginLoader.all()')

        all_matches = []
        found_in_cache = True

        legacy_excluding_builtin = set()
        for path_with_context in self._get_paths_with_context():
            matches = glob.glob(to_native(os.path.join(path_with_context.path, "*.py")))
            if not path_with_context.internal:
                legacy_excluding_builtin.update(matches)
            # we sort within each path, but keep path precedence from config
            all_matches.extend(sorted(matches, key=os.path.basename))

        loaded_modules = set()
        for path in all_matches:

            name = os.path.splitext(path)[0]
            basename = os.path.basename(name)
            is_j2 = isinstance(self, Jinja2Loader)

            if path in legacy_excluding_builtin:
                fqcn = basename
            else:
                fqcn = f"ansible.builtin.{basename}"

            if is_j2:
                ref_name = path
            else:
                ref_name = fqcn

            if not is_j2 and basename in _PLUGIN_FILTERS[self.package]:
                # j2 plugins get processed in own class, here they would just be container files
                display.debug("'%s' skipped due to a defined plugin filter" % basename)
                continue

            if basename == '__init__' or (basename == 'base' and self.package == 'ansible.plugins.cache'):
                # cache has legacy 'base.py' file, which is wrapper for __init__.py
                display.debug("'%s' skipped due to reserved name" % name)
                continue

            if dedupe and ref_name in loaded_modules:
                # for j2 this is 'same file', other plugins it is basename
                display.debug("'%s' skipped as duplicate" % ref_name)
                continue

            loaded_modules.add(ref_name)

            if path_only:
                yield path
                continue

            if (cached_result := (self._plugin_instance_cache or {}).get(fqcn)) and cached_result[1].resolved:
                # Here just in case, but we don't call all() multiple times for vars plugins, so this should not be used.
                yield cached_result[0]
                continue

            if path not in self._module_cache:
                path_context = PluginPathContext(path, path not in legacy_excluding_builtin)
                load_context = PluginLoadContext(self.type, self.package)
                load_context.resolve_legacy(basename, {basename: path_context})

                try:
                    module = self._load_module_source(python_module_name=load_context._python_module_name, path=path)
                except Exception as e:
                    display.warning("Skipping plugin (%s), cannot load: %s" % (path, to_text(e)))
                    continue

                self._module_cache[path] = module
                found_in_cache = False
            else:
                module = self._module_cache[path]

            self._load_config_defs(basename, module, path)

            try:
                obj = getattr(module, self.class_name)
            except AttributeError as e:
                display.warning("Skipping plugin (%s) as it seems to be invalid: %s" % (path, to_text(e)))
                continue

            if self.base_class:
                # The import path is hardcoded and should be the right place,
                # so we are not expecting an ImportError.
                module = __import__(self.package, fromlist=[self.base_class])
                # Check whether this obj has the required base class.
                try:
                    plugin_class = getattr(module, self.base_class)
                except AttributeError:
                    continue
                if not issubclass(obj, plugin_class):
                    continue

            self._display_plugin_load(self.class_name, basename, self._searched_paths, path, found_in_cache=found_in_cache, class_only=class_only)

            if not class_only:
                try:
                    obj = obj(*args, **kwargs)
                except TypeError as e:
                    display.warning("Skipping plugin (%s) as it seems to be incomplete: %s" % (path, to_text(e)))

            self._update_object(obj=obj, name=basename, path=path, resolved=fqcn)

            if self._plugin_instance_cache is not None:
                needs_enabled = False
                if hasattr(obj, 'REQUIRES_ENABLED'):
                    needs_enabled = obj.REQUIRES_ENABLED
                if not needs_enabled:
                    # Use get_with_context to cache the plugin the first time we see it.
                    self.get_with_context(fqcn)[0]

            yield obj