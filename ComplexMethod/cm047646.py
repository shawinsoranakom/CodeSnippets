def __init__(self, *opts, **attrs):
        self.my_default = attrs.pop('my_default', None)
        self.cli_loadable = attrs.pop('cli_loadable', True)
        env_name = attrs.pop('env_name', None)
        self.env_name = env_name or ''
        self.file_loadable = attrs.pop('file_loadable', True)
        self.file_exportable = attrs.pop('file_exportable', self.file_loadable)
        self.nargs_ = attrs.get('nargs')
        if self.nargs_ == '?':
            const = attrs.pop('const', None)
            attrs['nargs'] = 1
        attrs.setdefault('metavar', attrs.get('type', 'string').upper())
        super().__init__(*opts, **attrs)
        if 'default' in attrs:
            self.config._log(logging.WARNING, "please use my_default= instead of default= with option %s", self)
        if self.file_exportable and not self.file_loadable:
            e = (f"it makes no sense that the option {self} can be exported "
                  "to the config file but not loaded from the config file")
            raise ValueError(e)
        is_new_option = False
        if self.dest and self.dest not in self.config.options_index:
            self.config.options_index[self.dest] = self
            is_new_option = True
        if self.nargs_ == '?':
            self.const = const
            for opt in self._short_opts + self._long_opts:
                self.config.optional_options[opt] = self
        if env_name is None and is_new_option and self.file_loadable:
            # generate an env_name for file_loadable settings that are in the index
            self.env_name = 'ODOO_' + self.dest.upper()
        elif env_name and not is_new_option:
            raise ValueError(f"cannot set env_name to an option that is not indexed: {self}")