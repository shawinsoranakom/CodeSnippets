def _post_copy(self, old_rec, new_rec):
        self.ensure_one()
        translated_fields = self._theme_translated_fields.get(old_rec._name, [])
        cur_lang = self.env.lang or 'en_US'
        valid_langs = set(code for code, _ in self.env['res.lang'].get_installed()) | {'en_US'}
        old_rec.flush_recordset()
        for (src_field, dst_field) in translated_fields:
            __, src_fname = src_field.split(',')
            dst_mname, dst_fname = dst_field.split(',')
            if dst_mname != new_rec._name:
                continue
            old_field = old_rec._fields[src_fname]
            old_stored_translations = old_field._get_stored_translations(old_rec)
            if not old_stored_translations:
                continue
            if old_field.translate is True:
                if old_rec[src_fname] != new_rec[dst_fname]:
                    continue
                new_rec.update_field_translations(dst_fname, {
                    k: v for k, v in old_stored_translations.items() if k in valid_langs and k != cur_lang
                })
            else:
                old_translations = {
                    k: old_stored_translations.get(f'_{k}', v)
                    for k, v in old_stored_translations.items()
                    if k in valid_langs
                }
                # {from_lang_term: {lang: to_lang_term}
                translation_dictionary = old_field.get_translation_dictionary(
                    old_translations.pop(cur_lang, old_translations['en_US']),
                    old_translations
                )
                # {lang: {old_term: new_term}
                translations = defaultdict(dict)
                for from_lang_term, to_lang_terms in translation_dictionary.items():
                    for lang, to_lang_term in to_lang_terms.items():
                        translations[lang][from_lang_term] = to_lang_term
                new_rec.with_context(install_filename='dummy').update_field_translations(dst_fname, translations)