def _iter_column_sql(
        self, column_db_type, params, model, field, field_db_params, include_default
    ):
        yield column_db_type
        if collation := field_db_params.get("collation"):
            yield self._collate_sql(collation)
        # Work out nullability.
        null = field.null
        # Add database default.
        if field.has_db_default():
            default_sql, default_params = self.db_default_sql(field)
            yield f"DEFAULT {default_sql}"
            params.extend(default_params)
            include_default = False
        # Include a default value, if requested.
        include_default = (
            include_default
            and not self.skip_default(field)
            and
            # Don't include a default value if it's a nullable field and the
            # default cannot be dropped in the ALTER COLUMN statement (e.g.
            # MySQL longtext and longblob).
            not (null and self.skip_default_on_alter(field))
        )
        if include_default:
            default_value = self.effective_default(field)
            if default_value is not None:
                column_default = "DEFAULT " + self._column_default_sql(field)
                if self.connection.features.requires_literal_defaults:
                    # Some databases can't take defaults as a parameter
                    # (Oracle, SQLite). If this is the case, the individual
                    # schema backend should implement prepare_default().
                    yield column_default % self.prepare_default(default_value)
                else:
                    yield column_default
                    params.append(default_value)
        # Oracle treats the empty string ('') as null, so coerce the null
        # option whenever '' is a possible value.
        if (
            field.empty_strings_allowed
            and not field.primary_key
            and self.connection.features.interprets_empty_strings_as_nulls
        ):
            null = True
        if field.generated:
            generated_sql, generated_params = self._column_generated_sql(field)
            params.extend(generated_params)
            yield generated_sql
        elif not null:
            yield "NOT NULL"
        elif not self.connection.features.implied_column_null:
            yield "NULL"
        if field.primary_key:
            yield "PRIMARY KEY"
        elif field.unique:
            yield "UNIQUE"
        # Optionally add the tablespace if it's an implicitly indexed column.
        tablespace = field.db_tablespace or model._meta.db_tablespace
        if (
            tablespace
            and self.connection.features.supports_tablespaces
            and field.unique
        ):
            yield self.connection.ops.tablespace_sql(tablespace, inline=True)
        if self.connection.features.supports_comments_inline and field.db_comment:
            yield self._comment_sql(field.db_comment)