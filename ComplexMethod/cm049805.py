def reset_template(self):
        """Resets the Template with values given in source file. We ignore the case of
        template being overridden in another modules because it is extremely less likely
        to happen. This method also tries to reset the translation terms for the current
        user lang (all langs are not supported due to costly file operation). """
        expr = "//*[local-name() = $tag and (@id = $xml_id or @id = $external_id)]"
        templates_with_missing_source = []
        lang_false = {code: False for code, _ in self.env['res.lang'].get_installed() if code != 'en_US'}
        for template in self.filtered('template_fs'):
            external_id = template.get_external_id().get(template.id)
            module, xml_id = external_id.split('.')
            fullpath = file_path(template.template_fs)
            if fullpath:
                for field_name, field in template._fields.items():
                    if field.translate is True:
                        template.update_field_translations(field_name, lang_false)
                doc = etree.parse(fullpath)
                for rec in doc.xpath(expr, tag='record', xml_id=xml_id, external_id=external_id):
                    # We don't have a way to pass context while loading record from a file, so we use this hack
                    # to pass the context key that is needed to reset the fields not available in data file
                    rec.set('context', json.dumps({'reset_template': 'True'}))
                    obj = xml_import(template.env, module, {}, mode='init', xml_filename=fullpath)
                    obj._tag_record(rec)
                    template._override_translation_term(module, [xml_id, external_id])
            else:
                templates_with_missing_source.append(template.display_name)
        if templates_with_missing_source:
            raise UserError(_("The following email templates could not be reset because their related source files could not be found:\n- %s", "\n- ".join(templates_with_missing_source)))