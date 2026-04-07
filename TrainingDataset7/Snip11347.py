def _process_as_sqlite(self, sql, params, connection, key_transforms=None):
        json_path = self._get_json_path(connection, key_transforms)
        datatype_values = ",".join(
            [repr(value) for value in connection.ops.jsonfield_datatype_values]
        )
        return (
            "(CASE WHEN JSON_TYPE(%s, %%s) IN (%s) "
            "THEN JSON_TYPE(%s, %%s) ELSE JSON_EXTRACT(%s, %%s) END)"
        ) % (sql, datatype_values, sql, sql), (*params, json_path) * 3