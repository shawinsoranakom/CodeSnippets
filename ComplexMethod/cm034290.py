def _get_field_name_to_result_key_mapping(cls, *, for_callback: bool, for_round_trip: bool) -> dict[str, str]:
        mapping = {}

        for dc_field in dataclasses.fields(cls):
            metadata = t.cast(FieldSettings, dc_field.metadata.get('ansible', _DEFAULT_FIELD_SETTINGS))

            if (
                metadata.destination is Destination.ANY
                or ((for_round_trip or for_callback) and metadata.destination is Destination.CALLBACK)
                or ((for_round_trip or not for_callback) and metadata.destination is Destination.NOT_CALLBACK)
            ):
                key = metadata.key or dc_field.name
                field_name = key if hasattr(cls, key) else dc_field.name  # properties matching the exported key take precedence over the field during export

                mapping[field_name] = key

        return mapping