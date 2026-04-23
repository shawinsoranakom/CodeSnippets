def _apply_json_ignore_schema(cls, data, ignore_schema):
        assert data.__class__ is ignore_schema.__class__, "Type of data and ignore_schema must match"

        if isinstance(ignore_schema, dict):
            for schema_key, schema_value in ignore_schema.items():
                if schema_key in data:
                    if schema_value == '___ignore___':
                        data[schema_key] = '___ignore___'
                    elif data[schema_key]:  # schema_value is a dict or a list, and the corresponding value is not None
                        cls._apply_json_ignore_schema(data[schema_key], schema_value)
        elif isinstance(ignore_schema, list):
            if len(ignore_schema) == 1:
                # if there's only one dictionary, apply it to every item in the `data` list
                for data_child in data:
                    cls._apply_json_ignore_schema(data_child, ignore_schema[0])
            else:
                # otherwise, the length of the schema must match the data, and go through them as pairs
                assert len(ignore_schema) == len(data), "Length of list of ignore_schema and data must match"
                for i in range(len(ignore_schema)):
                    cls._apply_json_ignore_schema(data[i], ignore_schema[i])