def _alter_column_type_sql(
        self, model, old_field, new_field, new_type, old_collation, new_collation
    ):
        """
        Hook to specialize column type alteration for different backends,
        for cases when a creation type is different to an alteration type
        (e.g. SERIAL in PostgreSQL, PostGIS fields).

        Return a 2-tuple of: an SQL fragment of (sql, params) to insert into
        an ALTER TABLE statement and a list of extra (sql, params) tuples to
        run once the field is altered.
        """
        other_actions = []
        if collate_sql := self._collate_sql(
            new_collation, old_collation, model._meta.db_table
        ):
            collate_sql = f" {collate_sql}"
        else:
            collate_sql = ""
        # Comment change?
        comment_sql = ""
        if self.connection.features.supports_comments and not new_field.many_to_many:
            if old_field.db_comment != new_field.db_comment:
                # PostgreSQL and Oracle can't execute 'ALTER COLUMN ...' and
                # 'COMMENT ON ...' at the same time.
                sql, params = self._alter_column_comment_sql(
                    model, new_field, new_type, new_field.db_comment
                )
                if sql:
                    other_actions.append((sql, params))
            if new_field.db_comment:
                comment_sql = self._comment_sql(new_field.db_comment)
        return (
            (
                self.sql_alter_column_type
                % {
                    "column": self.quote_name(new_field.column),
                    "type": new_type,
                    "collation": collate_sql,
                    "comment": comment_sql,
                },
                [],
            ),
            other_actions,
        )