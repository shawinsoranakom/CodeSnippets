def _has_cycle(self, field_name=None) -> bool:
        """
        Return whether the records in ``self`` are in a loop by following the
        given relationship of the field.
        By default the **parent** field is used as the relationship.

        Note that since the method does not use EXCLUSIVE LOCK for the sake of
        performance, loops may still be created by concurrent transactions.

        :param field_name: optional field name (default: ``self._parent_name``)
        :return: **True** if a loop was found, **False** otherwise.
        """
        if not field_name:
            field_name = self._parent_name

        field = self._fields.get(field_name)
        if not field:
            raise ValueError(f'Invalid field_name: {field_name!r}')

        if not (
            field.type in ('many2many', 'many2one')
            and field.comodel_name == self._name
            and field.store
        ):
            raise ValueError(f'Field must be a many2one or many2many relation on itself: {field_name!r}')

        if not self.ids:
            return False

        # must ignore 'active' flag, ir.rules, etc.
        # direct recursive SQL query with cycle detection for performance
        self.flush_model([field_name])
        if field.type == 'many2many':
            relation = field.relation
            column1 = field.column1
            column2 = field.column2
        else:
            relation = self._table
            column1 = 'id'
            column2 = field_name
        cr = self.env.cr
        cr.execute(SQL(
            """
            WITH RECURSIVE __reachability AS (
                SELECT %(col1)s AS source, %(col2)s AS destination
                FROM %(rel)s
                WHERE %(col1)s IN %(ids)s AND %(col2)s IS NOT NULL
            UNION
                SELECT r.source, t.%(col2)s
                FROM __reachability r
                JOIN %(rel)s t ON r.destination = t.%(col1)s AND t.%(col2)s IS NOT NULL
            )
            SELECT 1 FROM __reachability
            WHERE source = destination
            LIMIT 1
            """,
            ids=tuple(self.ids),
            rel=SQL.identifier(relation),
            col1=SQL.identifier(column1),
            col2=SQL.identifier(column2),
        ))
        return bool(cr.fetchone())