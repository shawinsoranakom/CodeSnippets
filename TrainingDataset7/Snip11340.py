def compile_json_path_final_key(self, connection, key_transform):
        return connection.ops.compile_json_path([key_transform], include_root=False)