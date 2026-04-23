def _load_file_options(self, rcfile):
        self._file_options.clear()
        p = ConfigParser.RawConfigParser()
        try:
            p.read([rcfile])
            for (name, value) in p.items('options'):
                if name == 'without_demo':
                    name = 'with_demo'
                    value = str(self._check_without_demo(None, 'without_demo', value))
                option = self.options_index.get(name)
                if not option:
                    if name not in self.aliases:
                        self._log(logging.WARNING,
                            "unknown option %r in the config file at "
                            "%s, option stored as-is, without parsing",
                            name, self['config'],
                        )
                    self._file_options[name] = value
                    continue
                if not option.file_loadable:
                    continue
                if (
                    value in ('False', 'false')
                    and option.action not in ('store_true', 'store_false', 'callback')
                    and option.nargs_ != '?'
                ):
                    # "False" used to be the my_default of many non-bool options
                    self._log(logging.WARNING, "option %s reads %r in the config file at %s but isn't a boolean option, skip", name, value, self['config'])
                    continue
                self._file_options[name] = self.parse(name, value)
        except IOError:
            pass
        except ConfigParser.NoSectionError:
            pass