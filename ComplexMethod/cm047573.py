def get_field_translations(self, field_name: str, langs: Collection[str] | None = None) -> tuple[list[dict[str, str]], dict[str, typing.Any]]:
        """ Get model/model_term translations for records.

        :param field_name: field name
        :param langs: languages

        :return: (translations, context) where
            translations: list of dicts like [{"lang": lang, "source": source_term, "value": value_term}]
            context: {"translation_type": "text"/"char", "translation_show_source": True/False}
        """
        self.ensure_one()
        field = self._fields[field_name]
        # We don't forbid reading inactive/non-existing languages,
        langs = set(langs or [l[0] for l in self.env['res.lang'].get_installed()])
        self_lang = self.with_context(check_translations=True, prefetch_langs=True)
        val_en = self_lang.with_context(lang='en_US')[field_name]
        if not field.translate:
            translations = []
        elif field.translate is True:
            translations = [{
                'lang': lang,
                'source': val_en,
                'value': self_lang.with_context(lang=lang)[field_name]
            } for lang in langs]
        else:
            translation_dictionary = field.get_translation_dictionary(
                val_en, {lang: self_lang.with_context(lang=lang)[field_name] for lang in langs}
            )
            translations = [{
                'lang': lang,
                'source': term_en,
                'value': term_lang if term_lang != term_en else ''
            } for term_en, translations in translation_dictionary.items()
                for lang, term_lang in translations.items()]
        context = {}
        context['translation_type'] = 'text' if field.type in ['text', 'html'] else 'char'
        context['translation_show_source'] = callable(field.translate)

        return translations, context