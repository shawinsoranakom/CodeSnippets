def _sql_error_to_message_generic(self, exc: psycopg2.Error) -> str:
        """ Convert a database exception to a generic user error message. """
        diag = exc.diag
        unknown = self.env._('Unknown')
        model_string = self.env['ir.model']._get(self._name).name or self._description
        info = {
            'model_display': f"'{model_string}' ({self._name})",
            'table_name': diag.table_name,
            'constraint_name': diag.constraint_name,
        }
        if self._table == diag.table_name:
            columns = get_columns_from_sql_diagnostics(self.env.cr, diag, check_registry=True)
        else:
            columns = get_columns_from_sql_diagnostics(self.env.cr, diag)
            info['model_display'] = unknown
        if not columns:
            info['field_display'] = unknown
        elif len(columns) == 1 and (field := self._fields.get(columns[0])):
            field_string = field._description_string(self.env)
            info['field_display'] = f"'{field_string}' ({field.name})"
        else:
            info['field_display'] = f"'{format_list(self.env, columns)}'"

        if isinstance(exc, psycopg2.errors.NotNullViolation):
            return self.env._(
                "Missing required value for the field %(field_display)s.\n"
                "Model: %(model_display)s\n"
                "- create/update: a mandatory field is not set\n"
                "- delete: another model requires the record being deleted, you can archive it instead\n",
                **info,
            )

        if isinstance(exc, psycopg2.errors.ForeignKeyViolation):
            if len(columns) != 1:
                info['field_display'] = info['constraint_name']
            return self.env._(
                "Another model is using the record you are trying to delete.\n\n"
                "The troublemaker is: %(model_display)s\n"
                "Thanks to the following constraint: %(field_display)s\n"
                "How about archiving the record instead?",
                **info,
            )

        if isinstance(exc, psycopg2.errors.UniqueViolation) and columns:
            column_names = [self._fields[f].string if f in self._fields else f for f in columns]
            info['field_display'] = f"'{', '.join(columns)}' ({format_list(self.env, column_names)})"
            info['detail'] = diag.message_detail  # contains conflicting key and value
            return self.env._("The value for %(field_display)s already exists.\n\nDetail: %(detail)s\n", **info)

        # No good message can be created for psycopg2.errors.CheckViolation

        # fallback
        return exception_to_unicode(exc)