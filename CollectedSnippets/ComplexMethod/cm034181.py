def execute_init(self):
        """Create initial configuration"""

        seen = {}
        data = []
        config_entries = self._list_entries_from_args()
        plugin_types = config_entries.pop('PLUGINS', None)

        if context.CLIARGS['format'] == 'ini':
            sections = self._get_settings_ini(config_entries, seen)

            if plugin_types:
                for ptype in plugin_types:
                    plugin_sections = self._get_settings_ini(plugin_types[ptype], seen)
                    for s in plugin_sections:
                        if s in sections:
                            sections[s].extend(plugin_sections[s])
                        else:
                            sections[s] = plugin_sections[s]

            if sections:
                for section in sections.keys():
                    data.append('[%s]' % section)
                    for key in sections[section]:
                        data.append(key)
                        data.append('')
                    data.append('')

        elif context.CLIARGS['format'] in ('env', 'vars'):  # TODO: add yaml once that config option is added
            data = self._get_settings_vars(config_entries, context.CLIARGS['format'])
            if plugin_types:
                for ptype in plugin_types:
                    for plugin in plugin_types[ptype].keys():
                        data.extend(self._get_settings_vars(plugin_types[ptype][plugin], context.CLIARGS['format']))

        self.pager(to_text('\n'.join(data), errors='surrogate_or_strict'))