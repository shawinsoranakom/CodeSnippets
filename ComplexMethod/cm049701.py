def _copy_field_terms_translations(self, records_from, name_field_from, record_to, name_field_to):
        """ Copy model terms translations from ``records_from.name_field_from``
        to ``record_to.name_field_to`` for all activated languages if the term
        in ``record_to.name_field_to`` is untranslated (the term matches the
        one in the current language).

        For instance, copy the translations of a
        ``product.template.html_description`` field to a ``ir.ui.view.arch_db``
        field.

        The method takes care of read and write access of both records/fields.
        """
        record_to.check_access('write')
        field_from = records_from._fields[name_field_from]
        field_to = record_to._fields[name_field_to]
        record_to._check_field_access(field_to, 'write')

        error_callable_msg = "'translate' property of field %r is not callable"
        if not callable(field_from.translate):
            raise TypeError(error_callable_msg % field_from)
        if not callable(field_to.translate):
            raise TypeError(error_callable_msg % field_to)
        if not field_to.store:
            raise ValueError("Field %r is not stored" % field_to)

        # This will also implicitly check for `read` access rights
        if not record_to[name_field_to] or not any(records_from.mapped(name_field_from)):
            return

        lang_env = self.env.lang or 'en_US'
        langs = {lang for lang, _ in self.env['res.lang'].get_installed()}

        # 1. Get translations
        records_from.flush_model([name_field_from])
        records_from = records_from.with_context(check_translations=True)
        record_to = record_to.with_context(check_translations=True)
        existing_translation_dictionary = field_to.get_translation_dictionary(
            record_to[name_field_to],
            {lang: record_to.with_context(prefetch_langs=True, lang=lang)[name_field_to] for lang in langs if lang != lang_env}
        )
        extra_translation_dictionary = {}
        for record_from in records_from:
            extra_translation_dictionary.update(field_from.get_translation_dictionary(
                record_from[name_field_from],
                {lang: record_from.with_context(prefetch_langs=True, lang=lang)[name_field_from] for lang in langs if lang != lang_env}
            ))
        for term, extra_translation_values in extra_translation_dictionary.items():
            existing_translation_values = existing_translation_dictionary.setdefault(term, {})
            # Update only default translation values that aren't customized by the user.
            for lang, extra_translation in extra_translation_values.items():
                if existing_translation_values.get(lang, term) == term:
                    existing_translation_values[lang] = extra_translation
        translation_dictionary = existing_translation_dictionary

        # The `en_US` jsonb value should always be set, even if english is not
        # installed. If we don't do this, the custom snippet `arch_db` will only
        # have a `fr_BE` key but no `en_US` key.
        langs.add('en_US')

        # 2. Set translations
        new_value = {
            lang: field_to.translate(lambda term: translation_dictionary.get(term, {}).get(lang), record_to[name_field_to])
            for lang in langs
        }
        record_to.env.cache.update_raw(record_to, field_to, [new_value], dirty=True)
        # Call `write` to trigger compute etc (`modified()`)
        record_to.with_context(check_translations=False)[name_field_to] = new_value[lang_env]