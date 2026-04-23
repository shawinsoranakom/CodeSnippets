def _get_translation_upgrade_queries(cr, field):
    """ Return a pair of lists ``migrate_queries, cleanup_queries`` of SQL queries. The queries in
    ``migrate_queries`` do migrate the data from table ``_ir_translation`` to the corresponding
    field's column, while the queries in ``cleanup_queries`` remove the corresponding data from
    table ``_ir_translation``.
    """
    from odoo.modules.registry import Registry  # noqa: PLC0415
    Model = Registry(cr.dbname)[field.model_name]
    translation_name = f"{field.model_name},{field.name}"
    migrate_queries = []
    cleanup_queries = []

    if field.translate is True:
        emtpy_src = """'{"en_US": ""}'::jsonb"""
        query = f"""
            WITH t AS (
                SELECT it.res_id as res_id, jsonb_object_agg(it.lang, it.value) AS value, bool_or(imd.noupdate) AS noupdate
                  FROM _ir_translation it
             LEFT JOIN ir_model_data imd
                    ON imd.model = %s AND imd.res_id = it.res_id AND imd.module != '__export__'
                 WHERE it.type = 'model' AND it.name = %s AND it.state = 'translated'
              GROUP BY it.res_id
            )
            UPDATE {Model._table} m
               SET "{field.name}" = CASE WHEN m."{field.name}" IS NULL THEN {emtpy_src} || t.value
                                         WHEN t.noupdate IS FALSE THEN t.value || m."{field.name}"
                                         ELSE m."{field.name}" || t.value
                                     END
              FROM t
             WHERE t.res_id = m.id
        """
        migrate_queries.append(cr.mogrify(query, [Model._name, translation_name]).decode())

        query = "DELETE FROM _ir_translation WHERE type = 'model' AND state = 'translated' AND name = %s"
        cleanup_queries.append(cr.mogrify(query, [translation_name]).decode())

    # upgrade model_terms translation: one update per field per record
    if callable(field.translate):
        cr.execute("SELECT code FROM res_lang WHERE active = 't'")
        languages = {l[0] for l in cr.fetchall()}
        query = f"""
            SELECT t.res_id, m."{field.name}", t.value, t.noupdate
              FROM t
              JOIN "{Model._table}" m ON t.res_id = m.id
        """
        if translation_name == 'ir.ui.view,arch_db':
            cr.execute("SELECT id from ir_module_module WHERE name = 'website' AND state='installed'")
            if cr.fetchone():
                query = f"""
                    SELECT t.res_id, m."{field.name}", t.value, t.noupdate, l.code
                      FROM t
                      JOIN "{Model._table}" m ON t.res_id = m.id
                      JOIN website w ON m.website_id = w.id
                      JOIN res_lang l ON w.default_lang_id = l.id
                    UNION
                    SELECT t.res_id, m."{field.name}", t.value, t.noupdate, 'en_US'
                      FROM t
                      JOIN "{Model._table}" m ON t.res_id = m.id
                     WHERE m.website_id IS NULL
                """
        cr.execute(f"""
            WITH t0 AS (
                -- aggregate translations by source term --
                SELECT res_id, lang, jsonb_object_agg(src, value) AS value
                  FROM _ir_translation
                 WHERE type = 'model_terms' AND name = %s AND state = 'translated'
              GROUP BY res_id, lang
            ),
            t AS (
                -- aggregate translations by lang --
                SELECT t0.res_id AS res_id, jsonb_object_agg(t0.lang, t0.value) AS value, bool_or(imd.noupdate) AS noupdate
                  FROM t0
             LEFT JOIN ir_model_data imd
                    ON imd.model = %s AND imd.res_id = t0.res_id
              GROUP BY t0.res_id
            )""" + query, [translation_name, Model._name])
        for id_, new_translations, translations, noupdate, *extra in cr.fetchall():
            if not new_translations:
                continue
            # new_translations contains translations updated from the latest po files
            src_value = new_translations.pop('en_US')
            src_terms = field.get_trans_terms(src_value)
            for lang, dst_value in new_translations.items():
                terms_mapping = translations.setdefault(lang, {})
                dst_terms = field.get_trans_terms(dst_value)
                for src_term, dst_term in zip(src_terms, dst_terms):
                    if src_term == dst_term or noupdate:
                        terms_mapping.setdefault(src_term, dst_term)
                    else:
                        terms_mapping[src_term] = dst_term
            new_values = {
                lang: field.translate(terms_mapping.get, src_value)
                for lang, terms_mapping in translations.items()
            }
            if "en_US" not in new_values:
                new_values["en_US"] = field.translate(lambda v: None, src_value)
            if extra and extra[0] not in new_values:
                new_values[extra[0]] = field.translate(lambda v: None, src_value)
            elif not extra:
                missing_languages = languages - set(translations)
                if missing_languages:
                    src_value = field.translate(lambda v: None, src_value)
                    for lang in sorted(missing_languages):
                        new_values[lang] = src_value
            query = f'UPDATE "{Model._table}" SET "{field.name}" = %s WHERE id = %s'
            migrate_queries.append(cr.mogrify(query, [Json(new_values), id_]).decode())

        query = "DELETE FROM _ir_translation WHERE type = 'model_terms' AND state = 'translated' AND name = %s"
        cleanup_queries.append(cr.mogrify(query, [translation_name]).decode())

    return migrate_queries, cleanup_queries