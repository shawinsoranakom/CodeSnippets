def sequence_reset_sql(self, style, model_list):
        from django.db import models

        output = []
        qn = self.quote_name
        for model in model_list:
            # Use `coalesce` to set the sequence for each model to the max pk
            # value if there are records, or 1 if there are none. Set the
            # `is_called` property (the third argument to `setval`) to true if
            # there are records (as the max pk value is already in use),
            # otherwise set it to false. Use pg_get_serial_sequence to get the
            # underlying sequence name from the table name and column name.

            for f in model._meta.local_fields:
                if isinstance(f, models.AutoField):
                    output.append(
                        "%s setval(pg_get_serial_sequence('%s','%s'), "
                        "coalesce(max(%s), 1), max(%s) %s null) %s %s;"
                        % (
                            style.SQL_KEYWORD("SELECT"),
                            style.SQL_TABLE(qn(model._meta.db_table)),
                            style.SQL_FIELD(f.column),
                            style.SQL_FIELD(qn(f.column)),
                            style.SQL_FIELD(qn(f.column)),
                            style.SQL_KEYWORD("IS NOT"),
                            style.SQL_KEYWORD("FROM"),
                            style.SQL_TABLE(qn(model._meta.db_table)),
                        )
                    )
                    # Only one AutoField is allowed per model, so don't bother
                    # continuing.
                    break
        return output