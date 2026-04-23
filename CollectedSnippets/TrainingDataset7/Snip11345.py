def _get_json_path(self, connection, key_transforms):
        if key_transforms is None:
            return "$"
        return connection.ops.compile_json_path(key_transforms)