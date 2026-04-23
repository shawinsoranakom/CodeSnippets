def save(self, overwrite=False, force_overwrite=False):
        """ Save translations to the database.

        For a record with 'noupdate' in ``ir_model_data``, its existing translations
        will be overwritten if ``force_overwrite or (not noupdate and overwrite)``.

        An existing translation means:
        * model translation: the ``jsonb`` value in database has the language code as key;
        * model terms translation: the term value in the language is different from the term value in ``en_US``.
        """
        if not self.model_translations and not self.model_terms_translations:
            return

        cr = self.cr
        env = self.env
        env.flush_all()

        for model_name, model_dictionary in self.model_terms_translations.items():
            Model = env[model_name]
            model_table = Model._table
            fields = Model._fields
            # field_name, {xmlid: {src: {lang: value}}}
            for field_name, field_dictionary in model_dictionary.items():
                field = fields.get(field_name)
                for sub_xmlids in split_every(cr.IN_MAX, field_dictionary.keys()):
                    # [module_name, imd_name, module_name, imd_name, ...]
                    params = []
                    for xmlid in sub_xmlids:
                        params.extend(xmlid.split('.', maxsplit=1))
                    cr.execute(f'''
                        SELECT m.id, imd.module || '.' || imd.name, m."{field_name}", imd.noupdate
                        FROM "{model_table}" m, "ir_model_data" imd
                        WHERE m.id = imd.res_id
                        AND ({" OR ".join(["(imd.module = %s AND imd.name = %s)"] * (len(params) // 2))})
                    ''', params)

                    # [id, translations, id, translations, ...]
                    params = []
                    for id_, xmlid, values, noupdate in cr.fetchall():
                        if not values:
                            continue
                        _value_en = values.get('_en_US', values['en_US'])
                        if not _value_en:
                            continue

                        # {src: {lang: value}}
                        record_dictionary = field_dictionary[xmlid]
                        langs = {lang for translations in record_dictionary.values() for lang in translations.keys()}
                        translation_dictionary = field.get_translation_dictionary(
                            _value_en,
                            {
                                k: values.get(f'_{k}', v)
                                for k, v in values.items()
                                if k in langs
                            }
                        )

                        if force_overwrite or (not noupdate and overwrite):
                            # overwrite existing translations
                            for term_en, translations in record_dictionary.items():
                                translation_dictionary[term_en].update(translations)
                        else:
                            # keep existing translations
                            for term_en, translations in record_dictionary.items():
                                translations.update({k: v for k, v in translation_dictionary[term_en].items() if v != term_en})
                                translation_dictionary[term_en] = translations

                        changed_values = {}
                        for lang in langs:
                            # translate and confirm model_terms translations
                            new_val = field.translate(lambda term: translation_dictionary.get(term, {}).get(lang), _value_en)
                            if values.get(lang, None) != new_val:
                                changed_values[lang] = new_val
                            if f'_{lang}' in values:
                                changed_values[f'_{lang}'] = None
                        if changed_values:
                            params.extend((id_, Json(changed_values)))
                    if params:
                        env.cr.execute(f"""
                            UPDATE "{model_table}" AS m
                            SET "{field_name}" = jsonb_strip_nulls("{field_name}" || t.value)
                            FROM (
                                VALUES {', '.join(['(%s, %s::jsonb)'] * (len(params) // 2))}
                            ) AS t(id, value)
                            WHERE m.id = t.id
                        """, params)

        self.model_terms_translations.clear()

        for model_name, model_dictionary in self.model_translations.items():
            Model = env[model_name]
            model_table = Model._table
            for field_name, field_dictionary in model_dictionary.items():
                for sub_field_dictionary in split_every(cr.IN_MAX, field_dictionary.items()):
                    # [xmlid, translations, xmlid, translations, ...]
                    params = []
                    for xmlid, translations in sub_field_dictionary:
                        params.extend([*xmlid.split('.', maxsplit=1), Json(translations)])
                    if not force_overwrite:
                        value_query = f"""CASE WHEN {overwrite} IS TRUE AND imd.noupdate IS FALSE
                        THEN m."{field_name}" || t.value
                        ELSE t.value || m."{field_name}"END"""
                    else:
                        value_query = f'm."{field_name}" || t.value'
                    env.cr.execute(f"""
                        UPDATE "{model_table}" AS m
                        SET "{field_name}" = {value_query}
                        FROM (
                            VALUES {', '.join(['(%s, %s, %s::jsonb)'] * (len(params) // 3))}
                        ) AS t(imd_module, imd_name, value)
                        JOIN "ir_model_data" AS imd
                        ON imd."model" = '{model_name}' AND imd.name = t.imd_name AND imd.module = t.imd_module
                        WHERE imd."res_id" = m."id"
                    """, params)

        self.model_translations.clear()

        env.invalidate_all()
        env.registry.clear_cache()
        if self.verbose:
            _logger.info("translations are loaded successfully")