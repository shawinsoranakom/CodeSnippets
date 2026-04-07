def compile_json_path_final_key(self, connection, key_transform):
        # Compile the final key without interpreting ints as array elements.
        return ".%s" % json.dumps(key_transform)