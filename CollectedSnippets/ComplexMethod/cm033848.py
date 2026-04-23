def load_callbacks(self):
        """
        Loads all available callbacks, with the exception of those which
        utilize the CALLBACK_TYPE option. When CALLBACK_TYPE is set to 'stdout',
        only one such callback plugin will be loaded.
        """

        if self._callback_plugins:
            return

        if not self._stdout_callback_name:
            raise AnsibleError("No stdout callback name provided.")

        stdout_callback = callback_loader.get(self._stdout_callback_name)

        if not stdout_callback:
            raise AnsibleError(f"Could not load {self._stdout_callback_name!r} callback plugin.")

        templar = TemplateEngine(loader=self._loader, variables=self._variable_manager._extra_vars)

        stdout_callback._init_callback_methods()
        _resolve_callback_option_variables(stdout_callback, self._variable_manager._extra_vars, templar)

        self._callback_plugins.append(stdout_callback)

        # get all configured loadable callbacks (adjacent, builtin)
        plugin_types = {plugin_type.ansible_name: plugin_type for plugin_type in callback_loader.all(class_only=True)}

        # add enabled callbacks that refer to collections, which might not appear in normal listing
        for c in C.CALLBACKS_ENABLED:
            # load all, as collection ones might be using short/redirected names and not a fqcn
            plugin = callback_loader.get(c, class_only=True)

            if plugin:
                # avoids incorrect and dupes possible due to collections
                plugin_types.setdefault(plugin.ansible_name, plugin)
            else:
                display.warning("Skipping callback plugin '%s', unable to load" % c)

        plugin_types.pop(stdout_callback.ansible_name, None)

        # for each callback in the list see if we should add it to 'active callbacks' used in the play
        for callback_plugin in plugin_types.values():
            callback_type = getattr(callback_plugin, 'CALLBACK_TYPE', '')
            callback_needs_enabled = getattr(callback_plugin, 'CALLBACK_NEEDS_ENABLED', getattr(callback_plugin, 'CALLBACK_NEEDS_WHITELIST', False))

            # try to get collection world name first
            cnames = getattr(callback_plugin, '_redirected_names', [])
            if cnames:
                # store the name the plugin was loaded as, as that's what we'll need to compare to the configured callback list later
                callback_name = cnames[0]
            else:
                # fallback to 'old loader name'
                (callback_name, ext) = os.path.splitext(os.path.basename(callback_plugin._original_path))

            display.vvvvv("Attempting to use '%s' callback." % (callback_name))
            if callback_type == 'stdout':
                # we only allow one callback of type 'stdout' to be loaded,
                display.vv("Skipping callback '%s', as we already have a stdout callback." % (callback_name))
                continue
            elif callback_name == 'tree' and self._run_tree:
                # TODO: remove special case for tree, which is an adhoc cli option --tree
                pass
            elif not self._run_additional_callbacks or (callback_needs_enabled and (
                # only run if not adhoc, or adhoc was specifically configured to run + check enabled list
                    C.CALLBACKS_ENABLED is None or callback_name not in C.CALLBACKS_ENABLED)):
                # 2.x plugins shipped with ansible should require enabling, older or non shipped should load automatically
                continue

            try:
                callback_obj = callback_plugin()
                # avoid bad plugin not returning an object, only needed cause we do class_only load and bypass loader checks,
                # really a bug in the plugin itself which we ignore as callback errors are not supposed to be fatal.
                if callback_obj:
                    callback_obj._init_callback_methods()
                    _resolve_callback_option_variables(callback_obj, self._variable_manager._extra_vars, templar)
                    self._callback_plugins.append(callback_obj)
                else:
                    display.warning("Skipping callback '%s', as it does not create a valid plugin instance." % callback_name)
                    continue
            except Exception as ex:
                display.error_as_warning(f"Failed to load callback plugin {callback_name!r}.", exception=ex)
                continue