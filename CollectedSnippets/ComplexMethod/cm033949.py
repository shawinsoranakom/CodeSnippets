def _read_config_data(self, path):
        """ validate config and set options as appropriate
            :arg path: path to common yaml format config file for this plugin
        """

        try:
            # avoid loader cache so meta: refresh_inventory can pick up config changes
            # if we read more than once, fs cache should be good enough
            config = self.loader.load_from_file(path, cache='none', trusted_as_template=True)
        except Exception as e:
            raise AnsibleParserError(to_native(e))

        # a plugin can be loaded via many different names with redirection- if so, we want to accept any of those names
        valid_names = getattr(self, '_redirected_names') or [self.NAME]

        if not config:
            # no data
            raise AnsibleParserError("%s is empty" % (to_native(path)))
        elif config.get('plugin') not in valid_names:
            # this is not my config file
            raise AnsibleParserError("Incorrect plugin name in file: %s" % config.get('plugin', 'none found'))
        elif not isinstance(config, Mapping):
            # configs are dictionaries
            raise AnsibleParserError('inventory source has invalid structure, it should be a dictionary, got: %s' % type(config))

        self.set_options(direct=config, var_options=self._vars)
        if 'cache' in self._options and self.get_option('cache'):
            cache_option_keys = [('_uri', 'cache_connection'), ('_timeout', 'cache_timeout'), ('_prefix', 'cache_prefix')]
            cache_options = dict((opt[0], self.get_option(opt[1])) for opt in cache_option_keys if self.get_option(opt[1]) is not None)
            self._cache = get_cache_plugin(self.get_option('cache_plugin'), **cache_options)

        return config