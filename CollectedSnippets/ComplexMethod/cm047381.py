def _get_inheriting_views(self):
        """
        Determine the views that inherit from the current recordset, and return
        them as a recordset, ordered by priority then by id.
        """
        if not self.ids:
            return self.browse()
        domain = self._get_inheriting_views_domain()
        query = self._search(domain)
        where_clause = query.where_clause
        assert query.from_clause == SQL.identifier('ir_ui_view'), f"Unexpected from clause: {query.from_clause}"

        field_names = [f.name for f in self._fields.values() if f.prefetch is True and not f.groups]
        aliased_names = SQL(', ').join(
            SQL("%s AS %s", self._field_to_sql('ir_ui_view', name), SQL.identifier(name))
            for name in field_names
        )

        query = SQL("""
            WITH RECURSIVE ir_ui_view_inherits AS (
                SELECT ir_ui_view.id, %(aliased_names)s
                FROM ir_ui_view
                WHERE id IN %(ids)s AND (%(where_clause)s)
            UNION
                SELECT ir_ui_view.id, %(aliased_names)s
                FROM ir_ui_view
                INNER JOIN ir_ui_view_inherits parent ON parent.id = ir_ui_view.inherit_id
                WHERE coalesce(ir_ui_view.model, '') = coalesce(parent.model, '')
                      AND ir_ui_view.mode = 'extension'
                      AND (%(where_clause)s)
            )
            SELECT
                v.id, %(field_names)s
            FROM ir_ui_view_inherits as v
            ORDER BY v.priority, v.id
        """,
            aliased_names=aliased_names,
            field_names=SQL(', ').join(SQL.identifier('v', f) for f in field_names),
            ids=tuple(self.ids), where_clause=where_clause)
        # ORDER BY v.priority, v.id:
        # 1/ sort by priority: abritrary value set by developers on some
        #    views to solve "dependency hell" problems and force a view
        #    to be combined earlier or later. e.g. all views created via
        #    studio have a priority=99 to be loaded last.
        # 2/ sort by view id: the order the views were inserted in the
        #    database. e.g. base views are placed before stock ones.

        rows = self.env.execute_query(query)
        if not rows:
            return self.browse()

        ids, *columns = zip(*rows)
        views = self.browse(ids)

        # optimization: fill in cache of retrieved fields
        for fname, column in zip(field_names, columns, strict=True):
            self._fields[fname]._insert_cache(views, column)

        return views