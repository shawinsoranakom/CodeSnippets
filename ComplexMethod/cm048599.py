def _get_untranslated_translatable_template_model_records(self, langs, companies):
        """Return information about the records of any model in TEMPLATE_MODELS (and belonging to companies) that need to be translated.
        Records are in need of translation if they have a translatable field which is missing a translation (into any of the languages given in langs).

        :param langs: The codes of the languages into which we want to translate the records.
        :type langs: list[str]
        :param companies: Records belonging to these companies will be considered.
        :type companies: Model<res.company>
        :return: The records which information will be returned are those records that have at least 1 untranslated translatable field.
                 A field is 'untranslated' if it does not have a translation for all languages in langs.
                 The returned value is a List of tuples:
                     (model, xmlid (without module prefix), module, dictionary from name to value for each translatable field)
        :rtype: list[tuple(str, str, str, dict[str, str])]
        """
        if not langs or not companies:
            return []

        company_ids = tuple(companies.ids)

        translatable_model_fields = self._get_translatable_template_model_fields()

        # Generate a list of queries; exactly 1 per model
        queries = []
        for model in TEMPLATE_MODELS:
            translatable_fields = translatable_model_fields[model]
            if not translatable_fields:
                continue
            company_id_field = 'company_ids' if model == 'account.account' else 'company_id'

            self.env[model].flush_model(['id', company_id_field] + translatable_model_fields[model])

            query = self.env[model]._search([(company_id_field, 'in', company_ids)], bypass_access=True)

            # We only want records that have at least 1 missing translation in any of its translatable fields
            missing_translation_clauses = [
                SQL("(%s ->> %s) IS NULL", SQL.identifier(query.table, field), lang)
                for field in translatable_fields
                for lang in langs
            ]

            translatable_field_column_args = []
            for field in translatable_fields:
                translatable_field_column_args.extend((SQL("%s", field), SQL.identifier(query.table, field)))

            queries.append(SQL(
                """
                 SELECT %(model)s AS model,
                        model_data.name AS xmlid,
                        model_data.module AS module,
                        json_build_object(%(translatable_field_column_args)s) AS fields
                   FROM %(from_clause)s
                   JOIN ir_model_data model_data ON model_data.model = %(model)s
                                                AND %(model_id)s = model_data.res_id
                  WHERE %(where_clause)s
                        AND (%(missing_translation_clauses)s)
                """,
                model=model,
                translatable_field_column_args=SQL(", ").join(translatable_field_column_args),
                from_clause=query.from_clause,
                model_id=SQL.identifier(query.table, 'id'),
                where_clause=query.where_clause or SQL("TRUE"),
                missing_translation_clauses=SQL(" OR ").join(missing_translation_clauses),
            ))

        query = (SQL(' UNION ALL ').join(queries))
        # the queried models have been flushed already as part of the loop building the queries per model
        self.env['ir.model.data'].flush_model(['res_id', 'model', 'name'])

        self.env.cr.execute(query)
        return self.env.cr.fetchall()