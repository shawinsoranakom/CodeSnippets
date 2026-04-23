def act_getfile(self):
        self.ensure_one()
        lang = self.lang if self.lang != NEW_LANG_KEY else False

        with io.BytesIO() as buf:
            if self.export_type == 'model':
                ids = self.env[self.model_name].search(ast.literal_eval(self.domain)).ids
                is_exported = trans_export_records(lang, self.model_name, ids, buf, self.format, self.env)
            else:
                mods = sorted(self.mapped('modules.name')) or ['all']
                is_exported = trans_export(lang, mods, buf, self.format, self.env)
            out = is_exported and base64.encodebytes(buf.getvalue())

        filename = 'new'
        if lang:
            filename = tools.get_iso_codes(lang)
        elif self.export_type == 'model':
            filename = self.model_name.replace('.', '_')
        elif len(mods) == 1:
            filename = mods[0]
        extension = self.format
        if not lang and extension == 'po':
            extension = 'pot'
        name = "%s.%s" % (filename, extension)

        self.write({'state': 'get', 'data': out, 'name': name})
        return {
            'name': self.env.ref('base.action_wizard_lang_export').name,
            'type': 'ir.actions.act_window',
            'res_model': 'base.language.export',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }