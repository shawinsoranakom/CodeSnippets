def _find_plugin_legacy(self, name, plugin_load_context, check_aliases=False, suffix=None):
        """Search library and various *_plugins paths in order to find the file.
        This was behavior prior to the existence of collections.
        """
        plugin_load_context.resolved = False

        if check_aliases:
            name = self._aliases.get(name, name)

        # The particular cache to look for modules within.  This matches the
        # requested mod_type
        pull_cache = self._plugin_path_cache[suffix]
        try:
            resolved = plugin_load_context.resolve_legacy(name=name, pull_cache=pull_cache)
            self._check_core_deprecation(name, plugin_load_context)

            return resolved
        except KeyError:
            # Cache miss.  Now let's find the plugin
            pass

        # TODO: Instead of using the self._paths cache (PATH_CACHE) and
        #       self._searched_paths we could use an iterator.  Before enabling that
        #       we need to make sure we don't want to add additional directories
        #       (add_directory()) once we start using the iterator.
        #       We can use _get_paths_with_context() since add_directory() forces a cache refresh.
        for path_with_context in (p for p in self._get_paths_with_context() if p.path not in self._searched_paths and os.path.isdir(to_bytes(p.path))):
            path = path_with_context.path
            b_path = to_bytes(path)
            display.debug('trying %s' % path)
            plugin_load_context.load_attempts.append(path)
            internal = path_with_context.internal
            try:
                full_paths = (os.path.join(b_path, f) for f in os.listdir(b_path))
            except OSError as e:
                display.warning("Error accessing plugin paths: %s" % to_text(e))

            for full_path in (to_native(f) for f in full_paths if os.path.isfile(f) and not f.endswith(b'__init__.py')):
                full_name = os.path.basename(full_path)

                # HACK: We have no way of executing python byte compiled files as ansible modules so specifically exclude them
                # FIXME: I believe this is only correct for modules and module_utils.
                # For all other plugins we want .pyc and .pyo should be valid
                if any(full_path.endswith(x) for x in C.MODULE_IGNORE_EXTS):
                    continue
                splitname = os.path.splitext(full_name)
                base_name = splitname[0]
                try:
                    extension = splitname[1]
                except IndexError:
                    extension = ''

                # everything downstream expects unicode
                full_path = to_text(full_path, errors='surrogate_or_strict')
                # Module found, now enter it into the caches that match this file
                if base_name not in self._plugin_path_cache['']:
                    self._plugin_path_cache[''][base_name] = PluginPathContext(full_path, internal)

                if full_name not in self._plugin_path_cache['']:
                    self._plugin_path_cache[''][full_name] = PluginPathContext(full_path, internal)

                if base_name not in self._plugin_path_cache[extension]:
                    self._plugin_path_cache[extension][base_name] = PluginPathContext(full_path, internal)

                if full_name not in self._plugin_path_cache[extension]:
                    self._plugin_path_cache[extension][full_name] = PluginPathContext(full_path, internal)

            self._searched_paths.add(path)
            try:
                resolved = plugin_load_context.resolve_legacy(name=name, pull_cache=pull_cache)
                self._check_core_deprecation(name, plugin_load_context)

                return resolved
            except KeyError:
                # Didn't find the plugin in this directory. Load modules from the next one
                pass

        # if nothing is found, try finding alias/deprecated
        if not name.startswith('_'):
            alias_name = '_' + name

            try:
                plugin_load_context.resolve_legacy(name=alias_name, pull_cache=pull_cache)
            except KeyError:
                pass
            else:
                display.deprecated(
                    msg=f'Plugin {name!r} automatically redirected to {alias_name!r}.',
                    help_text=f'Use {alias_name!r} instead of {name!r} to refer to the plugin.',
                    version='2.23',
                )

                return plugin_load_context

        # last ditch, if it's something that can be redirected, look for a builtin redirect before giving up
        candidate_fqcr = 'ansible.builtin.{0}'.format(name)
        if '.' not in name and AnsibleCollectionRef.is_valid_fqcr(candidate_fqcr):
            return self._find_fq_plugin(fq_name=candidate_fqcr, extension=suffix, plugin_load_context=plugin_load_context)

        return plugin_load_context.nope('{0} is not eligible for last-chance resolution'.format(name))