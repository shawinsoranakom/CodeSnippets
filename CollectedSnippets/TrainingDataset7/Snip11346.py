def _process_as_oracle(self, sql, params, connection, key_transforms=None):
        json_path = self._get_json_path(connection, key_transforms)
        if connection.features.supports_primitives_in_json_field:
            template = (
                "COALESCE("
                "JSON_VALUE(%s, q'\uffff%s\uffff'),"
                "JSON_QUERY(%s, q'\uffff%s\uffff' DISALLOW SCALARS)"
                ")"
            )
        else:
            template = (
                "COALESCE("
                "JSON_QUERY(%s, q'\uffff%s\uffff'),"
                "JSON_VALUE(%s, q'\uffff%s\uffff')"
                ")"
            )
        # Add paths directly into SQL because path expressions cannot be passed
        # as bind variables on Oracle. Use a custom delimiter to prevent the
        # JSON path from escaping the SQL literal. Each key in the JSON path is
        # passed through json.dumps() with ensure_ascii=True (the default),
        # which converts the delimiter into the escaped \uffff format. This
        # ensures that the delimiter is not present in the JSON path.
        sql = template % ((sql, json_path) * 2)
        return sql, params * 2