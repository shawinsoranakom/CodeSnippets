def _get_settings_ini(self, settings, seen):

        sections = {}
        for o in sorted(settings.keys()):

            opt = settings[o]

            if not isinstance(opt, Mapping):
                # recursed into one of the few settings that is a mapping, now hitting it's strings
                continue

            if not opt.get('description'):
                # its a plugin
                new_sections = self._get_settings_ini(opt, seen)
                for s in new_sections:
                    if s in sections:
                        sections[s].extend(new_sections[s])
                    else:
                        sections[s] = new_sections[s]
                continue

            if isinstance(opt['description'], str):
                desc = '# (%s) %s' % (opt.get('type', 'string'), opt['description'])
            else:
                desc = "# (%s) " % opt.get('type', 'string')
                desc += "\n# ".join(opt['description'])

            if 'ini' in opt and opt['ini']:
                entry = opt['ini'][-1]
                if entry['section'] not in seen:
                    seen[entry['section']] = []
                if entry['section'] not in sections:
                    sections[entry['section']] = []

                # avoid dupes
                if entry['key'] not in seen[entry['section']]:
                    seen[entry['section']].append(entry['key'])

                    default = self.config.template_default(opt.get('default', ''), get_constants())
                    if opt.get('type', '') == 'list' and not isinstance(default, str):
                        # python lists are not valid ini ones
                        default = ', '.join(default)
                    elif default is None:
                        default = ''

                    if context.CLIARGS.get('commented', False):
                        entry['key'] = ';%s' % entry['key']

                    key = desc + '\n%s=%s' % (entry['key'], default)

                    sections[entry['section']].append(key)

        return sections