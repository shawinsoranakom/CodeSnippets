def returning_columns(self, fields):
        if not fields:
            return "", ()
        field_names = []
        params = []
        for field in fields:
            field_names.append(
                "%s.%s"
                % (
                    self.quote_name(field.model._meta.db_table),
                    self.quote_name(field.column),
                )
            )
            params.append(BoundVar(field))
        return "RETURNING %s INTO %s" % (
            ", ".join(field_names),
            ", ".join(["%s"] * len(params)),
        ), tuple(params)