def write(self, records, value):
        if not self.translate or value is False or value is None:
            super().write(records, value)
            return
        cache_value = self.convert_to_cache(value, records)
        records = self._filter_not_equal(records, cache_value)
        if not records:
            return
        field_cache = self._get_cache(records.env)
        dirty_ids = records.env._field_dirty.get(self, ())

        # flush dirty None values
        dirty_records = records.filtered(lambda rec: rec.id in dirty_ids)
        if any(field_cache.get(record_id, SENTINEL) is None for record_id in dirty_records._ids):
            dirty_records.flush_recordset([self.name])

        dirty = self.store and any(records._ids)
        lang = self.translation_lang(records.env)

        # not dirty fields
        if not dirty:
            if self.compute and self.inverse and any(records._ids):
                # invalidate the values in other languages to force their recomputation
                self._update_cache(records.with_context(prefetch_langs=True), {lang: cache_value}, dirty=False)
            else:
                self._update_cache(records, cache_value, dirty=False)
            return

        # model translation
        if not callable(self.translate):
            # invalidate clean fields because them may contain fallback value
            clean_records = records.filtered(lambda rec: rec.id not in dirty_ids)
            clean_records.invalidate_recordset([self.name])
            self._update_cache(records, cache_value, dirty=True)
            if lang != 'en_US' and not records.env['res.lang']._get_data(code='en_US'):
                # if 'en_US' is not active, we always write en_US to make sure value_en is meaningful
                self._update_cache(records.with_context(lang='en_US'), cache_value, dirty=True)
            return

        # model term translation
        new_translations_list = []
        new_terms = set(self.get_trans_terms(cache_value))
        delay_translations = records.env.context.get('delay_translations')
        for record in records:
            # shortcut when no term needs to be translated
            if not new_terms:
                new_translations_list.append({'en_US': cache_value, lang: cache_value})
                continue
            # _get_stored_translations can be refactored and prefetches translations for multi records,
            # but it is really rare to write the same non-False/None/no-term value to multi records
            stored_translations = self._get_stored_translations(record)
            if not stored_translations:
                new_translations_list.append({'en_US': cache_value, lang: cache_value})
                continue
            old_translations = {
                k: stored_translations.get(f'_{k}', v)
                for k, v in stored_translations.items()
                if not k.startswith('_')
            }
            from_lang_value = old_translations.pop(lang, old_translations['en_US'])
            translation_dictionary = self.get_translation_dictionary(from_lang_value, old_translations)
            text2terms = defaultdict(list)
            for term in new_terms:
                if term_text := self.get_text_content(term):
                    text2terms[term_text].append(term)

            is_text = self.translate.is_text if hasattr(self.translate, 'is_text') else lambda term: True
            term_adapter = self.translate.term_adapter if hasattr(self.translate, 'term_adapter') else None
            for old_term in list(translation_dictionary.keys()):
                if old_term not in new_terms:
                    old_term_text = self.get_text_content(old_term)
                    matches = get_close_matches(old_term_text, text2terms, 1, 0.9)
                    if matches:
                        closest_term = get_close_matches(old_term, text2terms[matches[0]], 1, 0)[0]
                        if closest_term in translation_dictionary:
                            continue
                        old_is_text = is_text(old_term)
                        closest_is_text = is_text(closest_term)
                        if old_is_text or not closest_is_text:
                            if not closest_is_text and records.env.context.get("install_mode") and lang == 'en_US' and term_adapter:
                                adapter = term_adapter(closest_term)
                                if adapter(old_term) is None:  # old term and closest_term have different structures
                                     continue
                                translation_dictionary[closest_term] = {k: adapter(v) for k, v in translation_dictionary.pop(old_term).items()}
                            else:
                                translation_dictionary[closest_term] = translation_dictionary.pop(old_term)
            # pylint: disable=not-callable
            new_translations = {
                l: self.translate(lambda term: translation_dictionary.get(term, {l: None})[l], cache_value)
                for l in old_translations.keys()
            }
            if delay_translations:
                new_store_translations = stored_translations
                new_store_translations.update({f'_{k}': v for k, v in new_translations.items()})
                new_store_translations.pop(f'_{lang}', None)
            else:
                new_store_translations = new_translations
            new_store_translations[lang] = cache_value

            if not records.env['res.lang']._get_data(code='en_US'):
                new_store_translations['en_US'] = cache_value
                new_store_translations.pop('_en_US', None)
            new_translations_list.append(new_store_translations)
        for record, new_translation in zip(records.with_context(prefetch_langs=True), new_translations_list, strict=True):
            self._update_cache(record, new_translation, dirty=True)