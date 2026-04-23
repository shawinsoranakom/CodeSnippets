def condition_to_sql(self, field_expr: str, operator: str, value, model: BaseModel, alias: str, query: Query) -> SQL:
        # build the condition
        if self.translate and model.env.context.get('prefetch_langs'):
            model = model.with_context(prefetch_langs=False)
        base_condition = super().condition_to_sql(field_expr, operator, value, model, alias, query)

        # faster SQL for index trigrams
        if (
            self.translate
            and value
            and operator in ('in', 'like', 'ilike', '=like', '=ilike')
            and self.index == 'trigram'
            and model.pool.has_trigram
            and (
                isinstance(value, str)
                or (isinstance(value, COLLECTION_TYPES) and all(isinstance(v, str) for v in value))
            )
        ):
            # a prefilter using trigram index to speed up '=', 'like', 'ilike'
            # '!=', '<=', '<', '>', '>=', 'in', 'not in', 'not like', 'not ilike' cannot use this trick
            if operator == 'in' and len(value) == 1:
                value = value_to_translated_trigram_pattern(next(iter(value)))
            elif operator != 'in':
                value = pattern_to_translated_trigram_pattern(value)
            else:
                value = '%'

            if value == '%':
                return base_condition

            raw_sql_field = self.to_sql(model.with_context(prefetch_langs=True), alias)
            sql_left = SQL("jsonb_path_query_array(%s, '$.*')::text", raw_sql_field)
            sql_operator = SQL_OPERATORS['like' if operator == 'in' else operator]
            sql_right = SQL("%s", self.convert_to_column(value, model, validate=False))
            unaccent = model.env.registry.unaccent
            return SQL(
                "(%s%s%s AND %s)",
                unaccent(sql_left),
                sql_operator,
                unaccent(sql_right),
                base_condition,
            )
        return base_condition