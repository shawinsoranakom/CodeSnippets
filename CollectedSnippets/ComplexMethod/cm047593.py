def copy_translations(self, new: Self, excluded: Collection[str] = ()) -> None:
        """ Recursively copy the translations from original to new record

        :param self: the original record
        :param new: the new record (copy of the original one)
        :param excluded: a container of user-provided field names
        """
        old = self
        # avoid recursion through already copied records in case of circular relationship
        if '__copy_translations_seen' not in old.env.context:
            old = old.with_context(__copy_translations_seen=defaultdict(set))
        seen_map = old.env.context['__copy_translations_seen']
        if old.id in seen_map[old._name]:
            return
        seen_map[old._name].add(old.id)
        valid_langs = set(code for code, _ in self.env['res.lang'].get_installed()) | {'en_US'}

        for name, field in old._fields.items():
            if not field.copy:
                continue

            if field.inherited and field.related.split('.')[0] in excluded:
                # inherited fields that come from a user-provided parent record
                # must not copy translations, as the parent record is not a copy
                # of the old parent record
                continue

            if field.type == 'one2many' and field.name not in excluded:
                # we must recursively copy the translations for o2m; here we
                # rely on the order of the ids to match the translations as
                # foreseen in copy_data()
                old_lines = old[name].sorted(key='id')
                new_lines = new[name].sorted(key='id')
                for (old_line, new_line) in zip(old_lines, new_lines):
                    # don't pass excluded as it is not about those lines
                    old_line.copy_translations(new_line)

            elif field.translate and field.store and name not in excluded and old[name]:
                # for translatable fields we copy their translations
                old_stored_translations = field._get_stored_translations(old)
                if not old_stored_translations:
                    continue
                lang = self.env.lang or 'en_US'
                if field.translate is True:
                    new.update_field_translations(name, {
                        k: v for k, v in old_stored_translations.items() if k in valid_langs and k != lang
                    })
                else:
                    old_translations = {
                        k: old_stored_translations.get(f'_{k}', v)
                        for k, v in old_stored_translations.items()
                        if k in valid_langs
                    }
                    # {from_lang_term: {lang: to_lang_term}
                    translation_dictionary = field.get_translation_dictionary(
                        old_translations.pop(lang, old_translations['en_US']),
                        old_translations
                    )
                    # {lang: {old_term: new_term}}
                    translations = defaultdict(dict)
                    for from_lang_term, to_lang_terms in translation_dictionary.items():
                        for lang, to_lang_term in to_lang_terms.items():
                            translations[lang][from_lang_term] = to_lang_term
                    new.update_field_translations(name, translations)