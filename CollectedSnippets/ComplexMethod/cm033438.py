def validate_document_meta_fields(cls, meta_fields: dict | None):
        if meta_fields is None:
            return None

        if not isinstance(meta_fields, dict):
            raise PydanticCustomError("format_invalid", "Only dictionary type supported")
        for k, v in meta_fields.items():
            if isinstance(v, list):
                if not all(isinstance(i, (str, int, float)) for i in v):
                    raise PydanticCustomError("format_invalid", "The type is not supported in list: {v}", {"v":v})
            elif not isinstance(v, (str, int, float)):
                raise PydanticCustomError("format_invalid", "The type is not supported: {v}", {"v":v})
        return meta_fields