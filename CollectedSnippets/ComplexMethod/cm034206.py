def _list_plugins(self, plugin_type, content):
        DocCLI._prep_loader(plugin_type)

        coll_filter = self._get_collection_filter()
        plugins = _list_plugins_with_info(plugin_type, coll_filter)

        # Remove the internal ansible._protomatter plugins if getting all plugins
        if not coll_filter:
            plugins = {k: v for k, v in plugins.items() if not k.startswith('ansible._protomatter.')}

        # get appropriate content depending on option
        if content == 'dir':
            results = self._get_plugin_list_descriptions(plugins)
        elif content == 'files':
            results = {k: v.path for k, v in plugins.items()}
        else:
            results = {k: {} for k in plugins.keys()}
            self.plugin_list = set()  # reset for next iteration

        return results