def _load_module_terms(self, modules, langs, overwrite=False):
        """ Load PO files of the given modules for the given languages. """
        # load i18n files
        translation_importer = TranslationImporter(self.env.cr, verbose=False)

        for module_name in modules:
            if not Manifest.for_addon(module_name, display_warning=False):
                continue
            for lang in langs:
                for po_path in get_po_paths(module_name, lang):
                    _logger.info('module %s: loading translation file %s for language %s', module_name, po_path, lang)
                    translation_importer.load_file(po_path, lang)
                for data_path in get_datafile_translation_path(module_name):
                    translation_importer.load_file(data_path, lang, module=module_name)
                if lang != 'en_US' and lang not in translation_importer.imported_langs:
                    _logger.info('module %s: no translation for language %s', module_name, lang)

        translation_importer.save(overwrite=overwrite)