def on_conflict_suffix_sql(self, fields, on_conflict, update_fields, unique_fields):
        if (
            on_conflict == OnConflict.UPDATE
            and self.connection.features.supports_update_conflicts_with_target
        ):
            return "ON CONFLICT(%s) DO UPDATE SET %s" % (
                ", ".join(map(self.quote_name, unique_fields)),
                ", ".join(
                    [
                        f"{field} = EXCLUDED.{field}"
                        for field in map(self.quote_name, update_fields)
                    ]
                ),
            )
        return super().on_conflict_suffix_sql(
            fields,
            on_conflict,
            update_fields,
            unique_fields,
        )