def _load_cli_options(self, opt):
        # odoo.cli.command.main parses the config twice, the second time
        # without --addons-path but expect the value to be persisted
        addons_path = self._cli_options.pop('addons_path', None)
        self._cli_options.clear()
        if addons_path is not None:
            self._cli_options['addons_path'] = addons_path

        keys = [
            option_name for option_name, option
            in self.options_index.items()
            if option.cli_loadable
            if option.action != 'append'
        ]

        for arg in keys:
            if getattr(opt, arg, None) is not None:
                self._cli_options[arg] = getattr(opt, arg)

        if opt.log_handler:
            self._cli_options['log_handler'] = [handler for comma in opt.log_handler for handler in comma]