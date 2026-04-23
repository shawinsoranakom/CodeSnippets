def _search_is_rotting(self, operator, value):
        if operator not in ['in', 'not in']:
            raise ValueError(self.env._('For performance reasons, use "=" operators on rotting fields.'))
        if not self._is_rotting_feature_enabled():
            raise UserError(self.env._('Model configuration does not support the rotting feature'))
        model_depends = [fname for fname in self._get_rotting_depends_fields() if '.' not in fname]
        self.flush_model(model_depends)  # flush fields to make sure DB is up to date
        self.env[self[self._track_duration_field]._name].flush_model(['rotting_threshold_days'])
        base_query = self._search(self._get_rotting_domain())

        # Our query needs to JOIN the stage field's table.
        # This JOIN needs to use the same alias as the base query to avoid non-matching alias issues
        # Note that query objects do not make their alias table available trivially,
        # but the alias can be inferred by consulting the _joins attribute and compare it to the result of make_alias()
        stage_table_alias_name = base_query.make_alias(self._table, self._track_duration_field)

        # We only need to add a JOIN if the stage table is not already present in the query's _joins attribute.
        from_add_join = ''
        if not base_query._joins or not stage_table_alias_name in base_query._joins:
            from_add_join = """
                INNER JOIN %(stage_table)s AS %(stage_table_alias_name)s
                    ON %(stage_table_alias_name)s.id = %(table)s.%(stage_field)s
            """

        # Items with a date_last_stage_update inferior to that number of months will not be returned by the search function.
        max_rotting_months = int(self.env['ir.config_parameter'].sudo().get_param('crm.lead.rot.max.months', default=12))

        # We use a F-string so that the from_add_join is added with its %s parameters before the query string is processed
        query = f"""
            WITH perishables AS (
                SELECT  %(table)s.id AS id,
                        (
                            %(table)s.date_last_stage_update + %(stage_table_alias_name)s.rotting_threshold_days * interval '1 day'
                        ) AS date_rot
                FROM %(from_clause)s
                    {from_add_join}
                WHERE
                    %(table)s.date_last_stage_update > %(today)s - INTERVAL '%(max_rotting_months)s months'
                    AND %(where_clause)s
            )
            SELECT id
            FROM perishables
            WHERE %(today)s >= date_rot

        """
        self.env.cr.execute(SQL(query,
            table=SQL.identifier(self._table),
            stage_table=SQL.identifier(self[self._track_duration_field]._table),
            stage_table_alias_name=SQL.identifier(stage_table_alias_name),
            stage_field=SQL.identifier(self._track_duration_field),
            today=self.env.cr.now(),
            where_clause=base_query.where_clause,
            from_clause=base_query.from_clause,
            max_rotting_months=max_rotting_months,
        ))
        rows = self.env.cr.dictfetchall()
        return [('id', operator, [r['id'] for r in rows])]