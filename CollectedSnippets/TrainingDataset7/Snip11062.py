def _get_default(self):
        if self.has_default():
            if callable(self.default):
                return self.default
            return lambda: self.default

        if self.has_db_default():
            from django.db.models.expressions import DatabaseDefault

            default = DatabaseDefault(self._db_default_expression, output_field=self)

            return lambda: default

        if (
            not self.empty_strings_allowed
            or self.null
            and not connection.features.interprets_empty_strings_as_nulls
        ):
            return return_None
        return str