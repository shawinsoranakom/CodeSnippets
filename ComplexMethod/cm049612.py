def _trigram_enumerate_words(self, search_details, search, limit):
        """
        Browses through all words that need to be compared to the search term.
        It extracts all words of every field associated to models in the fields_per_model parameter.
        The search is restricted to a records having the non-zero pg_trgm.word_similarity() score.

        :param search_details: obtained from `_search_get_details()`
        :param search: search term to which words must be matched against
        :param limit: maximum number of records fetched per model to build the word list
        :return: yields words
        """
        def get_similarity_subquery(model, fields, id_column, rel_table='', rel_joinkey=''):
            """ Build a subquery retrieving the greatest word_similarity between search and fields.
            It adds joins/left joins to the subquery when needed.

            :param model: current model used to retrieve the subquery table
            :param fields: sequence of fields used in similarity computation
            :id_column: name of the column used to get the correct ids.
                E.g. id for model=product_template, product_tmpl_id for model=product_product)
            :rel_table: name of the rel table when search_fields in search_details contains a Many2many.
            :rel_joinkey: name of the column used to join model._table with rel_table.
            """
            subquery = Query(self.env.cr, model._table, model._table_query)
            unaccent = self.env.registry.unaccent
            similarity = SQL(
                "GREATEST(%(similarities)s) as similarity",
                similarities=SQL(", ").join(
                    SQL("word_similarity(%(search)s, %(field)s)",
                        search=unaccent(SQL("%s", search)),
                        field=unaccent(model._field_to_sql(model._table, field, subquery)),
                    )
                    for field in fields
                ),
            )
            where_clauses = []
            for field_name in fields:
                field = model._fields[field_name]
                if field.translate:
                    alias = model._table
                    if field.related and not field.store:
                        _, field, alias = model._traverse_related_sql(model._table, field, subquery)
                    where_clauses.append(SQL("(%(search)s <%% %(jsonb_path)s AND %(search)s <%% (%(field)s))",
                        search=unaccent(SQL("%s", search)),
                        jsonb_path=unaccent(SQL("jsonb_path_query_array(%s, '$.*')::text", SQL.identifier(alias, field.name))),
                        field=unaccent(model._field_to_sql(model._table, field_name, subquery)),
                    ))
                else:
                    where_clauses.append(SQL("%(search)s <%% %(field)s",
                        search=unaccent(SQL("%s", search)),
                        field=unaccent(model._field_to_sql(model._table, field_name, subquery)),
                    ))
            subquery.add_where(SQL(' OR ').join(where_clauses))
            tbl_alias = model._table
            if rel_table:
                rel_alias = subquery.make_alias(rel_table, rel_joinkey)
                subquery.add_join("JOIN", rel_alias, rel_table, SQL("%s = %s",
                        SQL.identifier(rel_alias, rel_joinkey),
                        SQL.identifier(model._table, "id"),
                    ),
                )
                tbl_alias = rel_alias
            return subquery.select(SQL("%s as id", SQL.identifier(tbl_alias, id_column)), similarity)

        match_pattern = r'[\w./-]{%s,}' % min(4, len(search) - 3)
        # SET the `<%` similarity threshold to 0.3 for the current transaction (cluster default is 0.6)
        self.env.cr.execute("SET LOCAL pg_trgm.word_similarity_threshold to 0.3;")
        for search_detail in search_details:
            model_name, fields = search_detail['model'], search_detail['search_fields']
            model = self.env[model_name]
            if search_detail.get('requires_sudo'):
                model = model.sudo()
            domain = Domain.AND(search_detail['base_domain'])
            direct_fields = set(fields).intersection(model._fields)
            indirect_fields = self._search_get_indirect_fields(fields, model)
            # Group indirect_fields by comodel
            indirect_fields_info = defaultdict(dict)  # {comodel: {field_name: field_info}}
            for name, indirect_field in indirect_fields.items():
                indirect_fields_info[indirect_field['comodel']][name] = indirect_field
            subqueries = [get_similarity_subquery(model, direct_fields, 'id')]
            for comodel in indirect_fields_info:
                comodel_similarity_fields = set()
                id_column = rel_table = rel_joinkey = ''
                for indirect_field_info in indirect_fields_info[comodel].values():
                    direct_field = model._fields[indirect_field_info['direct']]
                    if direct_field.type == 'one2many':
                        comodel_similarity_fields.add(indirect_field_info['indirect'])
                        id_column = indirect_field_info['cofield']
                    elif direct_field.type == 'many2many':
                        comodel_similarity_fields.add(indirect_field_info['indirect'])
                        id_column = direct_field.column1
                        rel_table = direct_field.relation
                        rel_joinkey = direct_field.column2
                subqueries.append(get_similarity_subquery(comodel, comodel_similarity_fields, id_column, rel_table, rel_joinkey))
            query = SQL("""
                SELECT id,
                    MAX(similarity) as _best_similarity
                FROM (%s) sub
                GROUP BY id
                ORDER BY _best_similarity DESC
                LIMIT 1000
            """, SQL("\nUNION ALL\n").join(subqueries))  # UNION ALL allows to hit GIST indexes in subplans.
            self.env.cr.execute(query)
            ids = {row[0] for row in self.env.cr.fetchall()}
            domain = Domain.AND([domain, Domain([('id', 'in', list(ids))])])
            records = model.search_read(domain, direct_fields, limit=limit)
            for record in records:
                for value in record.values():
                    if isinstance(value, str):
                        value = value.lower()
                        yield from re.findall(match_pattern, value)
            if indirect_fields:
                records = model.search(domain, limit=limit)
                for indirect_field in indirect_fields:
                    for value in records.mapped(indirect_field):
                        if isinstance(value, str):
                            value = value.lower()
                            yield from re.findall(match_pattern, value)