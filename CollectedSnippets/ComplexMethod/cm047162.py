def _import(self, parsed_args):
        paths = OrderedSet(parsed_args.files)
        if invalid_paths := [path for path in paths if (
            not path.exists()
            or path.suffix not in IMPORT_EXTENSIONS
        )]:
            _logger.warning("Ignoring invalid paths: %s",
                ', '.join(str(path) for path in invalid_paths))
            paths -= set(invalid_paths)
        if not paths:
            self.import_parser.error("No valid path was provided")

        with Registry(parsed_args.db_name).cursor() as cr:
            env = Environment(cr, SUPERUSER_ID, {})
            translation_importer = TranslationImporter(cr)
            language = self._get_languages(env, [parsed_args.language])
            if not language:
                self.import_parser.error("No valid language has been provided")
            for path in paths:
                with path.open("rb") as infile:
                    translation_importer.load(infile, path.suffix.removeprefix('.'), language.code)
            translation_importer.save(overwrite=parsed_args.overwrite)