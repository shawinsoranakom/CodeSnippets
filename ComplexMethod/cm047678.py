def _export_imdinfo(self, model: str, imd_per_id: dict[int, ImdInfo]):
        records = self._get_translatable_records(imd_per_id.values())
        if not records:
            return

        env = records.env
        for record in records.with_context(check_translations=True):
            module = imd_per_id[record.id].module
            xml_name = "%s.%s" % (module, imd_per_id[record.id].name)
            for field_name, field in record._fields.items():
                # ir_actions_actions.name is filtered because unlike other inherited fields,
                # this field is inherited as postgresql inherited columns.
                # From our business perspective, the parent column is no need to be translated,
                # but it is need to be set to jsonb column, since the child columns need to be translated
                # And export the parent field may make one value to be translated twice in transifex
                #
                # Some ir_model_fields.field_description are filtered
                # because their fields have falsy attribute export_string_translation
                if (
                        not (field.translate and field.store)
                        or str(field) == 'ir.actions.actions.name'
                        or (str(field) == 'ir.model.fields.field_description'
                            and not env[record.model]._fields[record.name].export_string_translation)
                ):
                    continue
                name = model + "," + field_name
                value_en = record[field_name] or ''
                value_lang = record.with_context(lang=self._lang)[field_name] or ''
                trans_type = 'model_terms' if callable(field.translate) else 'model'
                try:
                    translation_dictionary = field.get_translation_dictionary(value_en, {self._lang: value_lang})
                except Exception:
                    _logger.exception("Failed to extract terms from %s %s", xml_name, name)
                    continue
                for term_en, term_langs in translation_dictionary.items():
                    term_lang = term_langs.get(self._lang)
                    self._push_translation(module, trans_type, name, xml_name, term_en, record_id=record.id, value=term_lang if term_lang != term_en else '')