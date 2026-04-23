def _install(self, parsed_args):
        with self._create_env_context(parsed_args.db_name) as env:

            valid_module_names = self._get_module_names(parsed_args.modules)
            installable_modules = self._get_modules(env, valid_module_names)
            if installable_modules:
                installable_modules.button_immediate_install()

            non_installable_modules = OrderedSet(
                module
                for module in parsed_args.modules
                if module not in set(installable_modules.mapped("name"))
            )
            importable_zipfiles = [
                fullpath
                for module in non_installable_modules
                if (fullpath := self._get_zip_path(module))
            ]
            if importable_zipfiles:
                if 'imported' not in env['ir.module.module']._fields:
                    _logger.warning("Cannot import data modules unless the `base_import_module` module is installed")
                else:
                    for importable_zipfile in importable_zipfiles:
                        env['ir.module.module']._import_zipfile(importable_zipfile)