def _render_settings(self, config):

        entries = []
        for setting in sorted(config):
            changed = (config[setting]['origin'] not in ('default', 'REQUIRED') and setting not in _IGNORE_CHANGED)

            if context.CLIARGS['format'] == 'display':
                if isinstance(config[setting], dict):
                    # proceed normally
                    value = config[setting]['value']
                    if config[setting]['origin'] == 'default' or setting in _IGNORE_CHANGED:
                        color = 'green'
                        value = self.config.template_default(value, get_constants())
                    elif config[setting]['origin'] == 'REQUIRED':
                        # should include '_terms', '_input', etc
                        color = 'red'
                    else:
                        color = 'yellow'
                    msg = "%s(%s) = %s" % (setting, config[setting]['origin'], value)
                else:
                    color = 'green'
                    msg = "%s(%s) = %s" % (setting, 'default', config[setting].get('default'))

                entry = stringc(msg, color)
            else:
                entry = {}
                for key in config[setting].keys():
                    if key == 'type':
                        continue
                    entry[key] = config[setting][key]

            if not context.CLIARGS['only_changed'] or changed:
                entries.append(entry)

        return entries