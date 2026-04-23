def _export(self, parsed_args):
        export_pot = 'pot' in parsed_args.languages

        if parsed_args.output:
            if len(parsed_args.languages) != 1:
                self.export_parser.error(
                    "When --output is specified, one single --language must be supplied")
            if parsed_args.output != '-':
                parsed_args.output = Path(parsed_args.output)
                if parsed_args.output.suffix not in EXPORT_EXTENSIONS:
                    self.export_parser.error(
                        f"Extensions allowed for --output are {', '.join(EXPORT_EXTENSIONS)}")
                if export_pot and parsed_args.output.suffix == '.csv':
                    self.export_parser.error(
                        "Cannot export template in .csv format, please specify a language.")

        if export_pot:
            parsed_args.languages.remove('pot')

        with Registry(parsed_args.db_name).cursor(readonly=True) as cr:
            env = Environment(cr, SUPERUSER_ID, {})

            # We want to log invalid parameters
            modules = env['ir.module.module'].search_fetch(
                [('name', 'in', parsed_args.modules)], ['name', 'state'])
            if not_found_module_names := set(parsed_args.modules) - set(modules.mapped("name")):
                _logger.warning("Ignoring not found modules: %s",
                    ", ".join(not_found_module_names))
            if not_installed_modules := modules.filtered(lambda x: x.state != 'installed'):
                _logger.warning("Ignoring not installed modules: %s",
                    ", ".join(not_installed_modules.mapped("name")))
                modules -= not_installed_modules
            if len(modules) < 1:
                self.export_parser.error("No valid module has been provided")
            module_names = modules.mapped("name")

            languages = self._get_languages(env, parsed_args.languages)
            languages_count = len(languages) + export_pot
            if languages_count == 0:
                self.export_parser.error("No valid language has been provided")

            if parsed_args.output:
                self._export_file(env, module_names, languages.code, parsed_args.output)
            else:
                # Po(t) files in the modules' i18n folders
                for module_name in module_names:
                    i18n_path = Path(get_module_path(module_name), 'i18n')
                    if export_pot:
                        path = i18n_path / f'{module_name}.pot'
                        self._export_file(env, [module_name], None, path)
                    for language in languages:
                        path = i18n_path / f'{language.iso_code}.po'
                        self._export_file(env, [module_name], language.code, path)