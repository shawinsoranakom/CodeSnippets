def sequence_reset_sql(self, style, model_list):
        output = []
        query = self._sequence_reset_sql
        for model in model_list:
            for f in model._meta.local_fields:
                if isinstance(f, AutoField):
                    no_autofield_sequence_name = self._get_no_autofield_sequence_name(
                        model._meta.db_table
                    )
                    table = self.quote_name(model._meta.db_table)
                    column = self.quote_name(f.column)
                    output.append(
                        query
                        % {
                            "no_autofield_sequence_name": no_autofield_sequence_name,
                            "table": table,
                            "column": column,
                            "table_name": strip_quotes(table),
                            "column_name": strip_quotes(column),
                            "suffix": self.connection.features.bare_select_suffix,
                        }
                    )
                    # Only one AutoField is allowed per model, so don't
                    # continue to loop
                    break
        return output