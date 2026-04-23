def _ensure_non_collection_wrappers(self, *args, **kwargs):
        if self._cached_non_collection_wrappers:
            return

        # get plugins from files in configured paths (multiple in each)
        for p_map in super(Jinja2Loader, self).all(*args, **kwargs):
            is_builtin = p_map.ansible_name.startswith('ansible.builtin.')

            # p_map is really object from file with class that holds multiple plugins
            plugins_list = getattr(p_map, self.method_map_name)
            try:
                plugins = plugins_list()
            except Exception as e:
                display.vvvv("Skipping %s plugins in '%s' as it seems to be invalid: %r" % (self.type, to_text(p_map._original_path), e))
                continue

            for plugin_name in plugins.keys():
                if '.' in plugin_name:
                    display.debug(f'{plugin_name} skipped in {p_map._original_path}; Jinja plugin short names may not contain "."')
                    continue

                if plugin_name in _PLUGIN_FILTERS[self.package]:
                    display.debug("%s skipped due to a defined plugin filter" % plugin_name)
                    continue

                fqcn = plugin_name
                collection = '.'.join(p_map.ansible_name.split('.')[:2]) if p_map.ansible_name.count('.') >= 2 else ''
                if not plugin_name.startswith(collection):
                    fqcn = f"{collection}.{plugin_name}"

                target_names = {plugin_name, fqcn}

                if is_builtin:
                    target_names.add(f'ansible.builtin.{plugin_name}')

                for target_name in target_names:
                    # the plugin class returned by the loader may host multiple Jinja plugins, but we wrap each plugin in
                    # its own surrogate wrapper instance here to ease the bookkeeping...
                    try:
                        wrapper = self._plugin_wrapper_type(plugins[plugin_name])
                    except Exception as ex:
                        wrapper = _DeferredPluginLoadFailure(ex)

                    self._update_object(obj=wrapper, name=target_name, path=p_map._original_path, resolved=fqcn)

                    if existing_plugin := self._cached_non_collection_wrappers.get(target_name):
                        display.debug(f'Jinja plugin {target_name} from {p_map._original_path} skipped; '
                                      f'shadowed by plugin from {existing_plugin._original_path})')
                        continue

                    self._cached_non_collection_wrappers[target_name] = wrapper