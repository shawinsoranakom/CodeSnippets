def _load_module_defaults(self, name, value):
        if value is None:
            return

        if not isinstance(value, list):
            value = [value]

        validated_module_defaults = []
        for defaults_dict in value:
            if not isinstance(defaults_dict, dict):
                raise AnsibleParserError(
                    "The field 'module_defaults' is supposed to be a dictionary or list of dictionaries, "
                    "the keys of which must be static action, module, or group names. Only the values may contain "
                    "templates. For example: {'ping': \"{{ ping_defaults }}\"}",
                    obj=defaults_dict,
                )

            validated_defaults_dict = {}
            for defaults_entry, defaults in defaults_dict.items():
                # module_defaults do not use the 'collections' keyword, so actions and
                # action_groups that are not fully qualified are part of the 'ansible.legacy'
                # collection. Update those entries here, so module_defaults contains
                # fully qualified entries.
                if defaults_entry.startswith('group/'):
                    group_name = defaults_entry.split('group/')[-1]

                    # The resolved action_groups cache is associated saved on the current Play
                    if self.play is not None:
                        group_name, dummy = self._resolve_group(group_name)

                    defaults_entry = 'group/' + group_name
                    validated_defaults_dict[defaults_entry] = defaults

                else:
                    if len(defaults_entry.split('.')) < 3:
                        defaults_entry = 'ansible.legacy.' + defaults_entry

                    resolved_action = self._resolve_action(defaults_entry)
                    if resolved_action:
                        validated_defaults_dict[resolved_action] = defaults

                    # If the defaults_entry is an ansible.legacy plugin, these defaults
                    # are inheritable by the 'ansible.builtin' subset, but are not
                    # required to exist.
                    if defaults_entry.startswith('ansible.legacy.'):
                        resolved_action = self._resolve_action(
                            defaults_entry.replace('ansible.legacy.', 'ansible.builtin.'),
                            mandatory=False
                        )
                        if resolved_action:
                            validated_defaults_dict[resolved_action] = defaults

            validated_module_defaults.append(validated_defaults_dict)

        return validated_module_defaults