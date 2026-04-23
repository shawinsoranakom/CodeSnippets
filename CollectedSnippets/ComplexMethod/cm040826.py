def _validate_value(value: Any, shape: Shape, field_name: str | None = None) -> None:
            # Document type accepts any JSON value
            if shape.type_name == "document":
                return

            if isinstance(shape, StructureShape):
                if not isinstance(value, dict):
                    # this is a defensive check, the mock result is loaded from JSON before, so should always be a dict
                    raise ValidationException(
                        f"Mock result must be a valid JSON object, but got '{type(value)}' instead"
                    )
                # Build a mapping from SFN-normalised member keys -> botocore member shapes
                members = shape.members
                sfn_key_to_member_shape: dict[str, Shape] = {
                    StateTaskService._to_sfn_cased(member_key): member_shape
                    for member_key, member_shape in members.items()
                }
                if field_validation_mode == MockResponseValidationMode.STRICT:
                    # Ensure required members are present, using SFN-normalised keys
                    for required_key in shape.required_members:
                        sfn_required_key = StateTaskService._to_sfn_cased(required_key)
                        if sfn_required_key not in value:
                            raise ValidationException(
                                f"Mock result schema validation error: Required field '{sfn_required_key}' is missing"
                            )
                # Validate present fields (match SFN-normalised keys to member shapes)
                for mock_field_name, mock_field_value in value.items():
                    member_shape = sfn_key_to_member_shape.get(mock_field_name)
                    if member_shape is None:
                        # Fields that are present in mock but are not in the API spec should not raise validation errors - forward compatibility
                        continue
                    _validate_value(mock_field_value, member_shape, mock_field_name)
                return

            if isinstance(shape, ListShape):
                if not isinstance(value, list):
                    _raise_type_error("an array", field_name)
                member_shape = shape.member
                for list_item in value:
                    _validate_value(list_item, member_shape, field_name)
                return

            if isinstance(shape, MapShape):
                if not isinstance(value, dict):
                    _raise_type_error("an object", field_name)
                value_shape = shape.value
                for _, map_item_value in value.items():
                    _validate_value(map_item_value, value_shape, field_name)
                return

            # Primitive shapes and others
            type_name = shape.type_name
            match type_name:
                case "string" | "timestamp":
                    if not isinstance(value, str):
                        _raise_type_error("a string", field_name)
                    # Validate enum if present
                    if isinstance(shape, StringShape):
                        enum = getattr(shape, "enum", None)
                        if enum and value not in enum:
                            raise ValidationException(
                                f"Mock result schema validation error: Field '{field_name}' is not an expected value"
                            )

                case "integer" | "long":
                    if not isinstance(value, int) or isinstance(value, bool):
                        _raise_type_error("a number", field_name)

                case "float" | "double":
                    if not (isinstance(value, (int, float)) or isinstance(value, bool)):
                        _raise_type_error("a number", field_name)

                case "boolean":
                    if not isinstance(value, bool):
                        _raise_type_error("a boolean", field_name)

                case "blob":
                    if not (isinstance(value, (str, bytes))):
                        _raise_type_error("a string", field_name)