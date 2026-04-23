def _update_field_translations(
        self,
        field_name: str,
        translations: dict[str, str | typing.Literal[False] | dict[str, str]],
        digest: Callable[[str], str] | None = None,
        source_lang: str = '',
    ) -> bool:
        """ Update the translations for a given field, with support for handling
        old terms using an optional digest function.

        :param field_name: The name of the field to update.
        :param translations: The translations to apply.
            If ``field.translate`` is ``True``, the dictionary should be in the
            format::

                {lang: new_value}

            where ``new_value`` can either be:

            * a ``str``, in which case the new translation for the specified
              language.
            * ``False``, in which case it removes the translation for the
                specified language and falls back to the latest en_US value.

            If ``field.translate`` is a callable, the dictionary should be in
            the format::

                {lang: {old_source_lang_term: new_term}}

            or (when ``digest`` is callable)::

                {lang: {digest(old_source_lang_term): new_term}}.

            where ``new_term`` can either be:

            * a non-empty ``str``, in which case the new translation of
              ``old_term`` for the specified language.
            * ``False`` or ``''``, in which case it removes the translation for
                the specified language and falls back to the old
                ``source_lang_term``.

        :param digest: An optional function to generate identifiers for old terms.
        :param source_lang: The language of ``old_source_lang_term`` in
            translations. Assumes ``'en_US'`` when it is not set / empty.
        """
        self.ensure_one()

        self.check_access('write')
        field = self._fields[field_name]
        self._check_field_access(field, 'write')

        valid_langs = set(code for code, _ in self.env['res.lang'].get_installed()) | {'en_US'}
        source_lang = source_lang or 'en_US'
        missing_langs = (set(translations) | {source_lang}) - valid_langs
        if missing_langs:
            raise UserError(
                _("The following languages are not activated: %(missing_names)s",
                missing_names=', '.join(missing_langs))
            )

        if not field.translate:
            return False  # or raise error

        if not field.store and not field.related and field.compute:
            # a non-related non-stored computed field cannot be translated, even if it has inverse function
            return False

        # Strictly speaking, a translated related/computed field cannot be stored
        # because the compute function only support one language
        # `not field.store` is a redundant logic.
        # But some developers store translated related fields.
        # In these cases, only all translations of the first stored translation field will be updated
        # For other stored related translated field, the translation for the flush language will be updated
        if field.related and not field.store:
            related_path, field_name = field.related.rsplit(".", 1)
            return self.mapped(related_path)._update_field_translations(field_name, translations, digest)

        if field.translate is True:
            # falsy values (except emtpy str) are used to void the corresponding translation
            if any(translation and not isinstance(translation, str) for translation in translations.values()):
                raise UserError(_("Translations for model translated fields only accept falsy values and str"))
            value_en = translations.get('en_US', True)
            if not value_en and value_en != '':
                translations.pop('en_US')
            translations = {
                lang: translation if isinstance(translation, str) else None
                for lang, translation in translations.items()
            }
            if not translations:
                return False

            translation_fallback = translations['en_US'] if translations.get('en_US') is not None \
                else translations[self.env.lang] if translations.get(self.env.lang) is not None \
                else next((v for v in translations.values() if v is not None), None)
            self.invalidate_recordset([field_name])
            self.env.cr.execute(SQL(
                """ UPDATE %(table)s
                    SET %(field)s = NULLIF(
                        jsonb_strip_nulls(%(fallback)s || COALESCE(%(field)s, '{}'::jsonb) || %(value)s),
                        '{}'::jsonb)
                    WHERE id = %(id)s
                """,
                table=SQL.identifier(self._table),
                field=SQL.identifier(field_name),
                fallback=Json({'en_US': translation_fallback}),
                value=Json(translations),
                id=self.id,
            ))
            self.modified([field_name])
        else:
            old_values = field._get_stored_translations(self)
            if not old_values:
                return False

            for lang in translations:
                # for languages to be updated, use the unconfirmed translated value to replace the language value
                if f'_{lang}' in old_values:
                    old_values[lang] = old_values.pop(f'_{lang}')
            translations = {lang: _translations for lang, _translations in translations.items() if _translations}

            old_source_lang_value = old_values[next(
                lang
                for lang in [f'_{source_lang}', source_lang, '_en_US', 'en_US']
                if lang in old_values)]
            old_values_to_translate = {
                lang: value
                for lang, value in old_values.items()
                if lang != source_lang and lang in translations
            }
            old_translation_dictionary = field.get_translation_dictionary(old_source_lang_value, old_values_to_translate)

            if digest:
                # replace digested old_en_term with real old_en_term
                digested2term = {
                    digest(old_en_term): old_en_term
                    for old_en_term in old_translation_dictionary
                }
                translations = {
                    lang: {
                        digested2term[src]: value
                        for src, value in lang_translations.items()
                        if src in digested2term
                    }
                    for lang, lang_translations in translations.items()
                }

            new_values = old_values
            for lang, _translations in translations.items():
                _old_translations = {src: values[lang] for src, values in old_translation_dictionary.items() if lang in values}
                _new_translations = {**_old_translations, **_translations}
                new_values[lang] = field.convert_to_cache(field.translate(_new_translations.get, old_source_lang_value), self)
            field._update_cache(self.with_context(prefetch_langs=True), new_values, dirty=True)

        # the following write is incharge of
        # 1. mark field as modified
        # 2. execute logics in the override `write` method
        # even if the value in cache is the same as the value written
        self[field_name] = self[field_name]
        return True