def _load(self, reader, lang, xmlids=None):
        if xmlids and not isinstance(xmlids, set):
            xmlids = set(xmlids)
        valid_langs = get_base_langs(lang)
        for row in reader:
            if not row.get('value') or not row.get('src'):  # ignore empty translations
                continue
            if row.get('type') == 'code':  # ignore code translations
                continue
            if row.get('lang', lang) not in valid_langs:
                continue
            model_name = row.get('imd_model')
            module_name = row['module']
            if model_name not in self.env:
                continue
            field_name = row['name'].split(',')[1]
            field = self.env[model_name]._fields.get(field_name)
            if not field or not field.translate or not field.store:
                continue
            xmlid = module_name + '.' + row['imd_name']
            if xmlids and xmlid not in xmlids:
                continue
            if row.get('type') == 'model' and field.translate is True:
                self.model_translations[model_name][field_name][xmlid][lang] = row['value']
                self.imported_langs.add(lang)
            elif row.get('type') == 'model_terms' and callable(field.translate):
                self.model_terms_translations[model_name][field_name][xmlid][row['src']][lang] = row['value']
                self.imported_langs.add(lang)