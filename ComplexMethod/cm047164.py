def _export_file(self, env, module_names, lang_code, path):
        source = module_names[0] if len(module_names) == 1 else 'modules'
        destination = 'stdout' if path == '-' else path
        _logger.info("Exporting %s (%s) to %s", source, lang_code or 'pot', destination)

        if destination == 'stdout':
            if not trans_export(lang_code, module_names, sys.stdout.buffer, 'po', env):
                _logger.warning("No translatable terms were found in %s.", module_names)
            return

        path.parent.mkdir(exist_ok=True)
        export_format = path.suffix.removeprefix('.')
        if export_format == 'pot':
            export_format = 'po'
        with path.open('wb') as outfile:
            if not trans_export(lang_code, module_names, outfile, export_format, env):
                _logger.warning("No translatable terms were found in %s.", module_names)