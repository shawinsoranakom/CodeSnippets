def _process_as_mysql(self, sql, params, connection, key_transforms=None):
        json_path = self._get_json_path(connection, key_transforms)
        return "JSON_EXTRACT(%s, %%s)" % sql, (*params, json_path)