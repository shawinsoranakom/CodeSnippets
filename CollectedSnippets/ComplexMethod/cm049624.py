def _load_module_terms(self, modules, langs, overwrite=False):
        """ Add missing website specific translation """
        res = super()._load_module_terms(modules, langs, overwrite=overwrite)

        if not langs or langs == ['en_US'] or not modules:
            return res

        # Add specific view translations

        # use the translation dic of the generic to translate the specific
        self.env.cr.flush()
        View = self.env['ir.ui.view']
        field = self.env['ir.ui.view']._fields['arch_db']
        batch_size = PREFETCH_MAX // 10
        self.env.cr.execute(""" SELECT generic.arch_db, specific.arch_db, specific.id
                                          FROM ir_ui_view generic
                                         INNER JOIN ir_ui_view specific
                                            ON generic.key = specific.key
                                         WHERE generic.website_id IS NULL AND generic.type = 'qweb'
                                         AND specific.website_id IS NOT NULL
                                         AND generic.arch_db IS NOT NULL
                                         AND specific.arch_db IS NOT NULL
                            """)
        while batch := self.env.cr.fetchmany(batch_size):
            for generic_arch_db, specific_arch_db, specific_id in batch:
                langs_update = (langs & generic_arch_db.keys()) - {'en_US'}
                if not langs_update:
                    continue
                # get dictionaries limited to the requested languages
                generic_arch_db_en = generic_arch_db.get('_en_US', generic_arch_db.get('en_US'))
                specific_arch_db_en = specific_arch_db.get('_en_US', specific_arch_db.get('en_US'))
                generic_arch_db_update = {k: generic_arch_db.get('_' + k, generic_arch_db[k]) for k in langs_update}
                specific_arch_db_update = {k: specific_arch_db.get('_' + k, specific_arch_db.get(k, specific_arch_db_en)) for k in langs_update}
                generic_translation_dictionary = field.get_translation_dictionary(generic_arch_db_en, generic_arch_db_update)
                specific_translation_dictionary = field.get_translation_dictionary(specific_arch_db_en, specific_arch_db_update)
                # update specific_translation_dictionary
                for term_en, specific_term_langs in specific_translation_dictionary.items():
                    if term_en not in generic_translation_dictionary:
                        continue
                    for lang, generic_term_lang in generic_translation_dictionary[term_en].items():
                        if overwrite or term_en == specific_term_langs[lang]:
                            specific_term_langs[lang] = generic_term_lang
                for lang in langs_update:
                    if specific_arch_db.get('_' + lang) == specific_arch_db.get(lang):
                        specific_arch_db.pop('_' + lang, None)
                    specific_arch_db[('_' + lang) if ('_' + lang) in specific_arch_db else lang] = field.translate(
                        lambda term: specific_translation_dictionary.get(term, {lang: None})[lang], specific_arch_db_en)
                field._update_cache(View.with_context(prefetch_langs=True).browse(specific_id), specific_arch_db, dirty=True)
        default_menu = self.env.ref('website.main_menu', raise_if_not_found=False)
        if not default_menu:
            return res

        lang_value_list = [SQL("%(lang)s, o_menu.name->>%(lang)s", lang=lang) for lang in langs if lang != 'en_US']
        update_jsonb_list = [SQL('jsonb_build_object(%s)', SQL(', ').join(items)) for items in split_every(50, lang_value_list)]
        update_jsonb = SQL(' || ').join(update_jsonb_list)
        o_menu_name = SQL('menu.name || %s' if overwrite else '%s || menu.name', update_jsonb)
        self.env.cr.execute(SQL(
            """
            UPDATE website_menu menu
               SET name = %(o_menu_name)s
              FROM website_menu o_menu
             INNER JOIN website_menu s_menu
                ON o_menu.name->>'en_US' = s_menu.name->>'en_US' AND o_menu.url = s_menu.url
             INNER JOIN website_menu root_menu
                ON s_menu.parent_id = root_menu.id AND root_menu.parent_id IS NULL
             WHERE o_menu.website_id IS NULL AND o_menu.parent_id = %(default_menu_id)s
               AND s_menu.website_id IS NOT NULL
               AND menu.id = s_menu.id
            """,
            o_menu_name=o_menu_name,
            default_menu_id=default_menu.id
        ))

        return res