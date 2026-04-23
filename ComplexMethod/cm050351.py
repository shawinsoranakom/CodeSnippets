def _load_module_terms(self, modules, langs, overwrite=False):
        super()._load_module_terms(modules, langs, overwrite=overwrite)

        translation_importer = TranslationImporter(self.env.cr, verbose=False)
        IrAttachment = self.env['ir.attachment']

        for module in modules:
            if Manifest.for_addon(module, display_warning=False):
                continue
            for lang in langs:
                for lang_ in get_base_langs(lang):
                    # Translations for imported data modules only works with imported po files
                    attachment = IrAttachment.sudo().search([
                        ('name', '=', f"{module}_{lang_}.po"),
                        ('url', '=', f"/{module}/i18n/{lang_}.po"),
                        ('type', '=', 'binary'),
                    ], limit=1)
                    if attachment.raw:
                        try:
                            with io.BytesIO(attachment.raw) as fileobj:
                                fileobj.name = attachment.name
                                translation_importer.load(fileobj, 'po', lang, module=module)
                        except Exception:   # noqa: BLE001
                            _logger.warning('module %s: failed to load translation attachment %s for language %s', module, attachment.name, lang)
                if lang != 'en_US' and lang not in translation_importer.imported_langs:
                    _logger.info('module %s: no translation for language %s', module, lang)

        translation_importer.save(overwrite=overwrite)