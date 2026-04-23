def _serialize_header_value(self, shape: Shape, value: Any):
        """Serializes a value for the location trait "header"."""
        if shape.type_name == "timestamp":
            datetime_obj = parse_to_aware_datetime(value)
            timestamp_format = shape.serialization.get(
                "timestampFormat", self.HEADER_TIMESTAMP_FORMAT
            )
            return self._convert_timestamp_to_str(datetime_obj, timestamp_format)
        elif shape.type_name == "list":
            converted_value = [
                self._serialize_header_value(shape.member, v) for v in value if v is not None
            ]
            return ",".join(converted_value)
        elif shape.type_name == "boolean":
            # Set the header value to "true" if the given value is truthy, otherwise set the header value to "false".
            return "true" if value else "false"
        elif is_json_value_header(shape):
            # Serialize with no spaces after separators to save space in
            # the header.
            return self._get_base64(json.dumps(value, separators=(",", ":")))
        else:
            return value