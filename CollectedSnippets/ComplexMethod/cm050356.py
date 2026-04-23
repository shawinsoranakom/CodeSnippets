def _extract_resource_attachment_translations(self, module, lang):
        yield from super()._extract_resource_attachment_translations(module, lang)
        if not self._get(module).imported:
            return
        self.env['ir.model.data'].flush_model()
        IrAttachment = self.env['ir.attachment']
        IrAttachment.flush_model()
        module_ = module.replace('_', r'\_')
        ids = [r[0] for r in self.env.execute_query(SQL(
            """
                SELECT ia.id
                FROM ir_attachment ia
                JOIN ir_model_data imd
                ON ia.id = imd.res_id
                AND imd.model = 'ir.attachment'
                AND imd.module = %(module)s
                AND ia.res_model = 'ir.ui.view'
                AND ia.res_field IS NULL
                AND ia.res_id IS NULL
                AND (ia.url ilike %(js_pattern)s or ia.url ilike %(xml_pattern)s)
                AND ia.type = 'binary'
                ORDER BY ia.url
            """,
            module=module,
            js_pattern=f'/{module_}/static/src/%.js',
            xml_pattern=f'/{module_}/static/src/%.xml',
        ))]
        attachments = IrAttachment.browse(OrderedSet(ids))
        if not attachments:
            return
        translations = self._get_imported_module_translations_for_webclient(module, lang)
        translations = {tran['id']: tran['string'] for tran in translations['messages']}
        for attachment in attachments.filtered('raw'):
            display_path = f'addons{attachment.url}'
            if attachment.url.endswith('js'):
                extract_method = 'odoo.tools.babel:extract_javascript'
                extract_keywords = {'_t': None}
            else:
                extract_method = 'odoo.tools.translate:babel_extract_qweb'
                extract_keywords = {}
            try:
                with io.BytesIO(attachment.raw) as fileobj:
                    for extracted in extract.extract(extract_method, fileobj, keywords=extract_keywords):
                        lineno, message, comments = extracted[:3]
                        value = translations.get(message, '')
                        # (module, ttype, name, res_id, source, comments, record_id, value)
                        yield (module, 'code', display_path, lineno, message, comments + [JAVASCRIPT_TRANSLATION_COMMENT], None, value)
            except Exception:  # noqa: BLE001
                _logger.exception("Failed to extract terms from attachment with url %s", attachment.url)