def get_config_value_and_origin(
            self,
            config: str,
            cfile: str | None = None,
            plugin_type: str | None = None,
            plugin_name: str | None = None,
            keys=None,
            variables=None,
            direct=None,
            *,
            templar: Templar | None = None
    ) -> tuple[str, t.Any]:
        """ Given a config key figure out the actual value and report on the origin of the settings """
        if cfile is None:
            # use default config
            cfile = self._config_file

        if config == 'CONFIG_FILE':
            return cfile, ''

        # Note: sources that are lists listed in low to high precedence (last one wins)
        value = None
        origin = None
        origin_ftype = None

        defs = self.get_configuration_definitions(plugin_type=plugin_type, name=plugin_name)
        if config in defs:

            aliases = defs[config].get('aliases', [])

            # direct setting via plugin arguments, can set to None so we bypass rest of processing/defaults
            if direct:
                if config in direct:
                    value = direct[config]
                    origin = 'Direct'
                else:
                    direct_aliases = [direct[alias] for alias in aliases if alias in direct]
                    if direct_aliases:
                        value = direct_aliases[0]
                        origin = 'Direct'

            if value is None and variables and defs[config].get('vars'):
                # Use 'variable overrides' if present, highest precedence, but only present when querying running play
                value, origin = self._loop_entries(variables, defs[config]['vars'])
                origin = 'var: %s' % origin

            # use playbook keywords if you have em
            if value is None and defs[config].get('keyword') and keys:
                value, origin = self._loop_entries(keys, defs[config]['keyword'])
                origin = 'keyword: %s' % origin

            # automap to keywords
            # TODO: deprecate these in favor of explicit keyword above
            if value is None and keys:
                if config in keys:
                    value = keys[config]
                    keyword = config

                elif aliases:
                    for alias in aliases:
                        if alias in keys:
                            value = keys[alias]
                            keyword = alias
                            break

                if value is not None:
                    origin = 'keyword: %s' % keyword

            if value is None and 'cli' in defs[config]:
                # avoid circular import .. until valid
                from ansible import context
                value, origin = self._loop_entries(context.CLIARGS, defs[config]['cli'])
                origin = 'cli: %s' % origin

            # env vars are next precedence
            if value is None and defs[config].get('env'):
                value, origin = self._loop_entries(os.environ, defs[config]['env'])
                value = _tags.TrustedAsTemplate().tag(value)
                origin = 'env: %s' % origin

            # try config file entries next, if we have one
            if self._parsers.get(cfile, None) is None:
                self._parse_config_file(cfile)

            # attempt to read from config file
            if value is None and cfile is not None:
                ftype = get_config_type(cfile)
                if ftype and defs[config].get(ftype):
                    try:
                        for entry in defs[config][ftype]:
                            # load from config
                            if ftype == 'ini':
                                temp_value = self._get_ini_config_value(cfile, entry.get('section', 'defaults'), entry['key'])
                            elif ftype == 'yaml':
                                raise AnsibleError('YAML configuration type has not been implemented yet')
                            else:
                                raise AnsibleError('Invalid configuration file type: %s' % ftype)

                            if temp_value is not None:
                                # set value and origin
                                value = temp_value
                                origin = cfile
                                origin_ftype = ftype
                                if 'deprecated' in entry:
                                    if ftype == 'ini':
                                        self.DEPRECATED.append(('[%s]%s' % (entry['section'], entry['key']), entry['deprecated']))
                                    else:
                                        raise AnsibleError('Unimplemented file type: %s' % ftype)

                    except Exception as e:
                        sys.stderr.write("Error while loading config %s: %s" % (cfile, to_native(e)))

            # set default if we got here w/o a value
            if value is None:
                if defs[config].get('required', False):
                    if not plugin_type or config not in INTERNAL_DEFS.get(plugin_type, {}):
                        raise AnsibleRequiredOptionError(f"Required config {_get_config_label(plugin_type, plugin_name, config)} not provided.")
                else:
                    origin = 'default'
                    value = self.template_default(defs[config].get('default'), variables, key_name=_get_config_label(plugin_type, plugin_name, config))

            if templar:
                value = templar.template(value)

            try:
                # ensure correct type, can raise exceptions on mismatched types
                value = ensure_type(value, defs[config].get('type'), origin=origin, origin_ftype=origin_ftype)
            except ValueError as ex:
                if origin.startswith('env:') and value == '':
                    # this is empty env var for non string so we can set to default
                    origin = 'default'
                    value = ensure_type(defs[config].get('default'), defs[config].get('type'), origin=origin, origin_ftype=origin_ftype)
                else:
                    raise AnsibleOptionsError(f'Config {_get_config_label(plugin_type, plugin_name, config)} from {origin!r} has an invalid value.') from ex

            # deal with restricted values
            if value is not None and 'choices' in defs[config] and defs[config]['choices'] is not None:
                invalid_choices = True  # assume the worst!
                if defs[config].get('type') == 'list':
                    # for a list type, compare all values in type are allowed
                    invalid_choices = not all(choice in defs[config]['choices'] for choice in value)
                else:
                    # these should be only the simple data types (string, int, bool, float, etc) .. ignore dicts for now
                    invalid_choices = value not in defs[config]['choices']

                if invalid_choices:

                    if isinstance(defs[config]['choices'], Mapping):
                        valid = ', '.join([to_text(k) for k in defs[config]['choices'].keys()])
                    elif isinstance(defs[config]['choices'], str):
                        valid = defs[config]['choices']
                    elif isinstance(defs[config]['choices'], Sequence):
                        valid = ', '.join([to_text(c) for c in defs[config]['choices']])
                    else:
                        valid = defs[config]['choices']

                    raise AnsibleOptionsError(f'Invalid value {value!r} for config {_get_config_label(plugin_type, plugin_name, config)}.',
                                              help_text=f'Valid values are: {valid}')

            # deal with deprecation of the setting
            if 'deprecated' in defs[config] and origin != 'default':
                self.DEPRECATED.append((config, defs[config].get('deprecated')))
        else:
            raise AnsibleUndefinedConfigEntry(f'No config definition exists for {_get_config_label(plugin_type, plugin_name, config)}.')

        if not _tags.Origin.is_tagged_on(value):
            value = _tags.Origin(description=f'<Config {origin}>').tag(value)

        return value, origin