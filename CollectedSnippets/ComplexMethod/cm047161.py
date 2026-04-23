def run(self, cmdargs):
        parsed_args = self.parser.parse_args(args=cmdargs)

        config_args = ['--no-http']
        if parsed_args.config:
            config_args += ['-c', parsed_args.config]
        if parsed_args.db_name:
            config_args += ['-d', parsed_args.db_name]

        config.parse_config(config_args, setup_logging=True)

        db_names = config['db_name']
        if not db_names or len(db_names) > 1:
            self.parser.error("Please provide a single database in the config file")
        parsed_args.db_name = db_names[0]

        match parsed_args.subcommand:
            case 'import':
                self._import(parsed_args)
            case 'export':
                self._export(parsed_args)
            case 'loadlang':
                self._loadlang(parsed_args)