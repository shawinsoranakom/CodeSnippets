def write(self, vals):
        lang_codes = self.mapped('code')
        if 'code' in vals and any(code != vals['code'] for code in lang_codes):
            raise UserError(_("Language code cannot be modified."))
        if vals.get('active') == False:
            if self.env['res.users'].with_context(active_test=True).search_count([('lang', 'in', lang_codes)], limit=1):
                raise UserError(_("Cannot deactivate a language that is currently used by users."))
            if self.env['res.partner'].with_context(active_test=True).search_count([('lang', 'in', lang_codes)], limit=1):
                raise UserError(_("Cannot deactivate a language that is currently used by contacts."))
            if self.env['res.users'].with_context(active_test=False).search_count([('lang', 'in', lang_codes)], limit=1):
                raise UserError(_("You cannot archive the language in which Odoo was setup as it is used by automated processes."))
            # delete linked ir.default specifying default partner's language
            self.env['ir.default'].discard_values('res.partner', 'lang', lang_codes)

        res = super().write(vals)

        if vals.get('active'):
            # If we activate a lang, set it's url_code to the shortest version
            # if possible
            for long_lang in self.filtered(lambda lang: '_' in lang.url_code):
                short_code = long_lang.code.split('_')[0]
                short_lang = self.with_context(active_test=False).search([
                    ('url_code', '=', short_code),
                ], limit=1)  # url_code is unique
                if (
                    short_lang
                    and not short_lang.active
                    # `code` should always be the long format containing `_` but
                    # there is a plan to change this in the future for `es_419`.
                    # This `and` is about not failing if it's the case one day.
                    and short_lang.code != short_code
                ):
                    short_lang.url_code = short_lang.code
                    long_lang.url_code = short_code

        self.env.flush_all()
        self.env.registry.clear_cache('stable')
        return res