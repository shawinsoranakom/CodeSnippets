def _load_code_translations(self, module_names=None, langs=None):
        try:
            # the table lock promises translations for a (module, language) will only be created once
            self.env.cr.execute(f'LOCK TABLE {self._table} IN EXCLUSIVE MODE NOWAIT')

            if module_names is None:
                module_names = self.env['ir.module.module'].search([('state', '=', 'installed')]).mapped('name')
            if langs is None:
                langs = [lang for lang, _ in self._get_languages() if lang != 'en_US']
            self.env.cr.execute(f'SELECT DISTINCT module, lang FROM {self._table}')
            loaded_code_translations = set(self.env.cr.fetchall())
            create_value_list = [
                {
                    'source': src,
                    'value': value,
                    'module': module_name,
                    'lang': lang,
                }
                for module_name in module_names
                for lang in langs
                if (module_name, lang) not in loaded_code_translations
                for src, value in CodeTranslations._get_code_translations(module_name, lang, lambda x: True).items()
            ]
            self.sudo().create(create_value_list)

        except psycopg2.errors.LockNotAvailable:
            return False

        return True