def _create_like_index_sql(self, model, field):
        """
        Return the statement to create an index with varchar operator pattern
        when the column type is 'varchar' or 'text', otherwise return None.
        """
        db_type = field.db_type(connection=self.connection)
        if db_type is not None and (field.db_index or field.unique):
            # Fields with database column types of `varchar` and `text` need
            # a second index that specifies their operator class, which is
            # needed when performing correct LIKE queries outside the
            # C locale. See #12234.
            #
            # The same doesn't apply to array fields such as varchar[size]
            # and text[size], so skip them.
            if "[" in db_type:
                return None
            # Non-deterministic collations on Postgresql don't support indexes
            # for operator classes varchar_pattern_ops/text_pattern_ops.
            collation_name = getattr(field, "db_collation", None)
            if not collation_name and field.is_relation:
                collation_name = getattr(field.target_field, "db_collation", None)
            if collation_name and not self._is_collation_deterministic(collation_name):
                return None
            if db_type.startswith("varchar"):
                return self._create_index_sql(
                    model,
                    fields=[field],
                    suffix="_like",
                    opclasses=["varchar_pattern_ops"],
                )
            elif db_type.startswith("text"):
                return self._create_index_sql(
                    model,
                    fields=[field],
                    suffix="_like",
                    opclasses=["text_pattern_ops"],
                )
        return None