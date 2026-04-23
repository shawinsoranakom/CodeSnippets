def _get_settings_vars(self, settings, subkey):

        data = []
        if context.CLIARGS['commented']:
            prefix = '#'
        else:
            prefix = ''

        for setting in settings:

            if not settings[setting].get('description'):
                continue

            default = self.config.template_default(settings[setting].get('default', ''), get_constants())
            if subkey == 'env':
                stype = settings[setting].get('type', '')
                if stype == 'boolean':
                    if default:
                        default = '1'
                    else:
                        default = '0'
                elif default:
                    if stype == 'list':
                        if not isinstance(default, str):
                            # python lists are not valid env ones
                            try:
                                default = ', '.join(default)
                            except Exception as e:
                                # list of other stuff
                                default = '%s' % to_native(default)
                    if isinstance(default, str) and not is_quoted(default):
                        default = shlex.quote(default)
                elif default is None:
                    default = ''

            if subkey in settings[setting] and settings[setting][subkey]:
                entry = settings[setting][subkey][-1]['name']
                if isinstance(settings[setting]['description'], str):
                    desc = settings[setting]['description']
                else:
                    desc = '\n#'.join(settings[setting]['description'])
                name = settings[setting].get('name', setting)
                data.append('# %s(%s): %s' % (name, settings[setting].get('type', 'string'), desc))

                # TODO: might need quoting and value coercion depending on type
                if subkey == 'env':
                    if entry.startswith('_ANSIBLE_'):
                        continue
                    data.append('%s%s=%s' % (prefix, entry, default))
                elif subkey == 'vars':
                    if entry.startswith('_ansible_'):
                        continue
                    data.append(prefix + '%s: %s' % (entry, to_text(yaml_short(default), errors='surrogate_or_strict')))
                data.append('')

        return data