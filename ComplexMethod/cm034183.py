def _get_plugin_configs(self, ptype, plugins):

        # prep loading
        loader = getattr(plugin_loader, '%s_loader' % ptype)

        # accumulators
        output = []
        config_entries = {}

        # build list
        if plugins:
            plugin_cs = []
            for plugin in plugins:
                p = loader.get(plugin, class_only=True)
                if p is None:
                    display.warning("Skipping %s as we could not find matching plugin" % plugin)
                else:
                    plugin_cs.append(loader.get(plugin, class_only=True))
        else:
            plugin_cs = loader.all(class_only=True)

        for plugin in plugin_cs:
            # in case of deprecation they diverge
            finalname = name = plugin._load_name
            if name.startswith('_'):
                if os.path.islink(plugin._original_path):
                    # skip alias
                    continue
                # deprecated, but use 'nice name'
                finalname = name.replace('_', '', 1) + ' (DEPRECATED)'

            # default entries per plugin
            config_entries[finalname] = self.config.get_configuration_definitions(ptype, name)

            try:
                # populate config entries by loading plugin
                dump = loader.get(name, class_only=True)
            except Exception as e:
                display.warning('Skipping "%s" %s plugin, as we cannot load plugin to check config due to : %s' % (name, ptype, to_native(e)))
                continue

            # actually get the values
            for setting in config_entries[finalname].keys():
                try:
                    v, o = C.config.get_config_value_and_origin(setting, cfile=self.config_file, plugin_type=ptype, plugin_name=name, variables=get_constants())
                except AnsibleRequiredOptionError:
                    v = None
                    o = 'REQUIRED'

                if v is None and o is None:
                    # not all cases will be error
                    o = 'REQUIRED'

                config_entries[finalname][setting] = {
                    'name': setting,
                    'value': v,
                    'origin': o,
                    'type': None
                }

            # pretty please!
            results = self._render_settings(config_entries[finalname])
            if results:
                if context.CLIARGS['format'] == 'display':
                    # avoid header for empty lists (only changed!)
                    output.append('\n%s:\n%s' % (finalname, '_' * len(finalname)))
                    output.extend(results)
                else:
                    output.append({finalname: results})

        return output