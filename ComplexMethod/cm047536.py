def convert_to_record(self, value, record):
        if value is None:
            return False
        if not self.translate:
            return value
        if isinstance(value, dict):
            lang = self.translation_lang(record.env)
            # raise a KeyError for the __get__ function
            value = value[lang]
        if (
            callable(self.translate)
            and record.env.context.get('edit_translations')
            and self.get_trans_terms(value)
        ):
            base_lang = record._get_base_lang()
            lang = record.env.lang or 'en_US'
            delay_translation = value != record.with_context(edit_translations=None, check_translations=None, lang=lang)[self.name]

            if lang != base_lang:
                base_value = record.with_context(edit_translations=None, check_translations=True, lang=base_lang)[self.name]
                base_terms = self.get_trans_terms(base_value)
                translated_terms = self.get_trans_terms(value) if value != base_value else base_terms
                if len(base_terms) != len(translated_terms):
                    # term number mismatch, ignore all translations
                    value = base_value
                    translated_terms = base_terms
                get_base = dict(zip(translated_terms, base_terms)).__getitem__
            else:
                get_base = lambda term: term

            # use a wrapper to let the frontend js code identify each term and
            # its metadata in the 'edit_translations' context
            def translate_func(term):
                source_term = get_base(term)
                translation_state = 'translated' if lang == base_lang or source_term != term else 'to_translate'
                translation_source_sha = sha256(source_term.encode()).hexdigest()
                return (
                    '<span '
                        f'''{'class="o_delay_translation" ' if delay_translation else ''}'''
                        f'data-oe-model="{markup_escape(record._name)}" '
                        f'data-oe-id="{markup_escape(record.id)}" '
                        f'data-oe-field="{markup_escape(self.name)}" '
                        f'data-oe-translation-state="{translation_state}" '
                        f'data-oe-translation-source-sha="{translation_source_sha}"'
                    '>'
                        f'{term}'
                    '</span>'
                )
            # pylint: disable=not-callable
            value = self.translate(translate_func, value)
        return value