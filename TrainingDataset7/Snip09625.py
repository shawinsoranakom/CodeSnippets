def __init__(self, param, cursor, strings_only=False):
        # With raw SQL queries, datetimes can reach this function
        # without being converted by DateTimeField.get_db_prep_value.
        if settings.USE_TZ and (
            isinstance(param, datetime.datetime)
            and not isinstance(param, Oracle_datetime)
        ):
            param = Oracle_datetime.from_datetime(param)

        string_size = 0
        has_boolean_data_type = (
            cursor.database.features.supports_boolean_expr_in_select_clause
        )
        if not has_boolean_data_type:
            # Oracle < 23c doesn't recognize True and False correctly.
            if param is True:
                param = 1
            elif param is False:
                param = 0
        if hasattr(param, "bind_parameter"):
            self.force_bytes = param.bind_parameter(cursor)
        elif isinstance(param, (bytes, datetime.timedelta)):
            self.force_bytes = param
        else:
            # To transmit to the database, we need Unicode if supported
            # To get size right, we must consider bytes.
            self.force_bytes = force_str(param, cursor.charset, strings_only)
            if isinstance(self.force_bytes, str):
                # We could optimize by only converting up to 4000 bytes here
                string_size = len(force_bytes(param, cursor.charset, strings_only))
        if hasattr(param, "input_size"):
            # If parameter has `input_size` attribute, use that.
            self.input_size = param.input_size
        elif string_size > 4000:
            # Mark any string param greater than 4000 characters as a CLOB.
            self.input_size = Database.DB_TYPE_CLOB
        elif isinstance(param, datetime.datetime):
            self.input_size = Database.DB_TYPE_TIMESTAMP
        elif has_boolean_data_type and isinstance(param, bool):
            self.input_size = Database.DB_TYPE_BOOLEAN
        else:
            self.input_size = None