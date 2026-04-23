def _update_transifex_url(self, translations):
        """ Update translations' Transifex URL

        :param translations: the translations to update, may be a recordset or a list of dicts.
            The elements of `translations` must have the fields/keys 'source', 'module', 'lang',
            and the field/key 'transifex_url' is updated on them.
        """

        # e.g. 'https://www.transifex.com/odoo/'
        base_url = self.env['ir.config_parameter'].sudo().get_param('transifex.project_url')
        if not base_url:
            return
        base_url = base_url.rstrip('/')

        res_langs = self.env['res.lang'].search([])
        lang_to_iso = {l.code: l.iso_code for l in res_langs}
        if not lang_to_iso:
            return

        projects = self._get_transifex_projects()
        if not projects:
            return

        for translation in translations:
            if not translation['source'] or translation['lang'] == 'en_US':
                continue

            lang_iso = lang_to_iso.get(translation['lang'])
            if not lang_iso:
                continue

            project = projects.get(translation['module'])
            if not project:
                continue

            # e.g. https://www.transifex.com/odoo/odoo-16/translate/#fr_FR/sale/42?q=text:'Sale+Order'
            # 42 is an arbitrary number to satisfy the transifex URL format
            source = werkzeug.urls.url_quote_plus(translation['source'][:50].replace("\n", "").replace("'", "\\'"))
            source = f"'{source}'" if "+" in source else source
            translation['transifex_url'] = f"{base_url}/{project}/translate/#{lang_iso}/{translation['module']}/42?q=text%3A{source}"