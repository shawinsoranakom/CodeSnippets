def update_build_config(self, build_config: dotdict, field_value: Any, field_name: str | None = None):
        if field_name == "number_of_fields":
            default_keys = ["code", "_type", "number_of_fields", "text_key", "text_key_validator"]
            try:
                field_value_int = int(field_value)
            except ValueError:
                return build_config
            existing_fields = {}
            if field_value_int > self.MAX_FIELDS:
                build_config["number_of_fields"]["value"] = self.MAX_FIELDS
                msg = (
                    f"Number of fields cannot exceed {self.MAX_FIELDS}. "
                    "Please adjust the number of fields to be within the allowed limit."
                )
                raise ValueError(msg)
            if len(build_config) > len(default_keys):
                # back up the existing template fields
                for key in build_config.copy():
                    if key not in default_keys:
                        existing_fields[key] = build_config.pop(key)

            for i in range(1, field_value_int + 1):
                key = f"field_{i}_key"
                if key in existing_fields:
                    field = existing_fields[key]
                    build_config[key] = field
                else:
                    field = DictInput(
                        display_name=f"Field {i}",
                        name=key,
                        info=f"Key for field {i}.",
                        input_types=["Message", "Data", "JSON"],
                    )
                    build_config[field.name] = field.to_dict()

            build_config["number_of_fields"]["value"] = field_value_int
        return build_config