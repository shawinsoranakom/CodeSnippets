def exclude_fields_from_api(key: str, value: Any):
        type_ = type(value)
        field = getattr(type(c_out), "model_fields", {}).get(key, None)
        json_schema_extra = field.json_schema_extra if field else None

        # case where 1st layer field needs to be excluded
        if (
            json_schema_extra
            and isinstance(json_schema_extra, dict)
            and json_schema_extra.get("exclude_from_api", None)
        ):
            delattr(c_out, key)

        # if it's a model with nested fields
        elif is_model(type_):
            for field_name, field in type_.model_fields.items():
                extra = getattr(field, "json_schema_extra", None)
                if (
                    extra
                    and isinstance(extra, dict)
                    and extra.get("exclude_from_api", None)
                ):
                    delattr(value, field_name)

                # if it's a yet a nested model we need to go deeper in the recursion
                elif is_model(getattr(field, "annotation", None)):
                    exclude_fields_from_api(field_name, getattr(value, field_name))