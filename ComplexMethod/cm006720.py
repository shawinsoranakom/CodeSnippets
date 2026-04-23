def _validate_schema_inputs(self, action_key: str) -> list[InputTypes]:
        """Convert the JSON schema for *action_key* into Langflow input objects."""
        # Skip validation for default/placeholder values
        if action_key in ("disabled", "placeholder", ""):
            logger.debug(f"Skipping schema validation for placeholder value: {action_key}")
            return []

        schema_dict = self._action_schemas.get(action_key)
        if not schema_dict:
            logger.warning(f"No schema found for action key: {action_key}")
            return []

        try:
            parameters_schema = schema_dict.get("input_parameters", {})
            if parameters_schema is None:
                logger.warning(f"Parameters schema is None for action key: {action_key}")
                return []

            # Check if parameters_schema has the expected structure
            if not isinstance(parameters_schema, dict):
                logger.warning(
                    f"Parameters schema is not a dict for action key: {action_key}, got: {type(parameters_schema)}"
                )
                return []

            # Validate parameters_schema has required structure before flattening
            if not parameters_schema.get("properties") and not parameters_schema.get("$defs"):
                # Create a minimal valid schema to avoid errors
                parameters_schema = {"type": "object", "properties": {}}

            # Sanitize the schema before passing to flatten_schema
            # Handle case where 'required' is explicitly None (causes "'NoneType' object is not iterable")
            if parameters_schema.get("required") is None:
                parameters_schema = parameters_schema.copy()  # Don't modify the original
                parameters_schema["required"] = []

            # Also get top-level required fields from original schema
            original_required = set(parameters_schema.get("required", []))

            try:
                # Preserve original descriptions before flattening to restore if lost
                original_descriptions = {}
                original_props = parameters_schema.get("properties", {})
                for prop_name, prop_schema in original_props.items():
                    if isinstance(prop_schema, dict) and "description" in prop_schema:
                        original_descriptions[prop_name] = prop_schema["description"]

                flat_schema = flatten_schema(parameters_schema)

                # Restore lost descriptions in flattened schema
                if flat_schema and isinstance(flat_schema, dict) and "properties" in flat_schema:
                    flat_props = flat_schema["properties"]
                    for field_name, field_schema in flat_props.items():
                        # Check if this field lost its description during flattening
                        if isinstance(field_schema, dict) and "description" not in field_schema:
                            # Try to find the original description
                            # Handle array fields like bcc[0] -> bcc
                            base_field_name = field_name.replace("[0]", "")
                            if base_field_name in original_descriptions:
                                field_schema["description"] = original_descriptions[base_field_name]
                            elif field_name in original_descriptions:
                                field_schema["description"] = original_descriptions[field_name]
            except (KeyError, TypeError, ValueError) as flatten_error:
                logger.error(f"flatten_schema failed for {action_key}: {flatten_error}")
                return []

            if flat_schema is None:
                logger.warning(f"Flat schema is None for action key: {action_key}")
                return []

            # Additional check for flat_schema structure
            if not isinstance(flat_schema, dict):
                logger.warning(f"Flat schema is not a dict for action key: {action_key}, got: {type(flat_schema)}")
                return []

            # Ensure flat_schema has the expected structure for create_input_schema_from_json_schema
            if flat_schema.get("type") != "object":
                logger.warning(f"Flat schema for {action_key} is not of type 'object', got: {flat_schema.get('type')}")
                # Fix the schema type if it's missing
                flat_schema["type"] = "object"

            if "properties" not in flat_schema:
                flat_schema["properties"] = {}

            # Clean up field names - remove [0] suffixes from array fields
            cleaned_properties = {}
            attachment_related_fields = set()  # Track fields that are attachment-related

            for field_name, field_schema in flat_schema.get("properties", {}).items():
                # Remove [0] suffix from field names (e.g., "bcc[0]" -> "bcc", "cc[0]" -> "cc")
                clean_field_name = field_name.replace("[0]", "")

                # Check if this field is attachment-related (contains "attachment." prefix)
                if clean_field_name.lower().startswith("attachment."):
                    attachment_related_fields.add(clean_field_name)
                    # Don't add individual attachment sub-fields to the schema
                    continue

                # Handle reserved attribute name conflicts
                if clean_field_name in self.RESERVED_ATTRIBUTES:
                    original_name = clean_field_name
                    clean_field_name = f"{self.app_name}_{clean_field_name}"
                    # Update the field schema description to reflect the name change
                    field_schema_copy = field_schema.copy()
                    original_description = field_schema.get("description", "")
                    field_schema_copy["description"] = (
                        f"{original_name.replace('_', ' ').title()} for {self.app_name.title()}: {original_description}"
                    ).strip()
                else:
                    # Use the original field schema for all other fields
                    field_schema_copy = field_schema

                # Preserve the full schema information, not just the type
                cleaned_properties[clean_field_name] = field_schema_copy

            # If we found attachment-related fields, add a single "attachment" field
            if attachment_related_fields:
                # Create a generic attachment field schema
                attachment_schema = {
                    "type": "string",
                    "description": "File attachment for the email",
                    "title": "Attachment",
                }
                cleaned_properties["attachment"] = attachment_schema

            # Update the flat schema with cleaned field names
            flat_schema["properties"] = cleaned_properties

            # Also update required fields to match cleaned names
            if flat_schema.get("required"):
                cleaned_required = []
                for field in flat_schema["required"]:
                    base = field.replace("[0]", "")
                    if base in self.RESERVED_ATTRIBUTES:
                        cleaned_required.append(f"{self.app_name}_{base}")
                    else:
                        cleaned_required.append(base)
                flat_schema["required"] = cleaned_required

            input_schema = create_input_schema_from_json_schema(flat_schema)
            if input_schema is None:
                logger.warning(f"Input schema is None for action key: {action_key}")
                return []

            # Additional safety check before calling schema_to_langflow_inputs
            if not hasattr(input_schema, "model_fields"):
                logger.warning(f"Input schema for {action_key} does not have model_fields attribute")
                return []

            if input_schema.model_fields is None:
                logger.warning(f"Input schema model_fields is None for {action_key}")
                return []

            result = schema_to_langflow_inputs(input_schema)

            # Process inputs to handle attachment fields and set advanced status
            if result:
                processed_inputs = []
                required_fields_set = set(flat_schema.get("required", []))

                # Get file upload fields from stored action data
                file_upload_fields = self._actions_data.get(action_key, {}).get("file_upload_fields", set())
                if attachment_related_fields:  # If we consolidated attachment fields
                    file_upload_fields = file_upload_fields | {"attachment"}

                # Identify top-level JSON parents (object/array) to render as single CodeInput
                top_props_for_json = set()
                props_dict = parameters_schema.get("properties", {}) if isinstance(parameters_schema, dict) else {}
                for top_name, top_schema in props_dict.items():
                    if isinstance(top_schema, dict) and top_schema.get("type") in {"object", "array"}:
                        top_props_for_json.add(top_name)

                for inp in result:
                    if hasattr(inp, "name") and inp.name is not None:
                        # Skip flattened subfields of JSON parents; handle array prefixes (e.g., parent[0].x)
                        raw_prefix = inp.name.split(".")[0]
                        base_prefix = raw_prefix.replace("[0]", "")
                        if base_prefix in top_props_for_json and ("." in inp.name or "[" in inp.name):
                            continue
                        # Check if this specific field is a file upload field
                        if inp.name.lower() in file_upload_fields or inp.name.lower() == "attachment":
                            # Replace with FileInput for file upload fields
                            file_input = FileInput(
                                name=inp.name,
                                display_name=getattr(inp, "display_name", inp.name.replace("_", " ").title()),
                                required=inp.name in required_fields_set,
                                advanced=inp.name not in required_fields_set,
                                info=getattr(inp, "info", "Upload file for this field"),
                                show=True,
                                file_types=[
                                    "csv",
                                    "txt",
                                    "doc",
                                    "docx",
                                    "xls",
                                    "xlsx",
                                    "pdf",
                                    "png",
                                    "jpg",
                                    "jpeg",
                                    "gif",
                                    "zip",
                                    "rar",
                                    "ppt",
                                    "pptx",
                                ],
                            )
                            processed_inputs.append(file_input)
                        else:
                            # Ensure proper display_name and info are set for regular fields
                            if not hasattr(inp, "display_name") or not inp.display_name:
                                inp.display_name = inp.name.replace("_", " ").title()

                            # Preserve description from schema if available
                            field_schema = flat_schema.get("properties", {}).get(inp.name, {})
                            schema_description = field_schema.get("description")
                            current_info = getattr(inp, "info", None)

                            # Use schema description if available, otherwise keep current info or create from name
                            if schema_description:
                                inp.info = schema_description
                            elif not current_info:
                                # Fallback: create a basic description from the field name if no description exists
                                inp.info = f"{inp.name.replace('_', ' ').title()} field"

                            # Set advanced status for non-file-upload fields
                            if inp.name not in required_fields_set:
                                inp.advanced = True

                            # Skip entity_id being mapped to user_id parameter
                            # Check both original name and renamed version
                            if inp.name in {"user_id", f"{self.app_name}_user_id"} and getattr(
                                self, "entity_id", None
                            ) == getattr(inp, "value", None):
                                continue

                            processed_inputs.append(inp)
                    else:
                        processed_inputs.append(inp)

                # Add single CodeInput for each JSON parent field
                props_dict = parameters_schema.get("properties", {}) if isinstance(parameters_schema, dict) else {}
                for top_name in top_props_for_json:
                    # Avoid duplicates if already present
                    if any(getattr(i, "name", None) == top_name for i in processed_inputs):
                        continue
                    top_schema = props_dict.get(top_name, {})
                    # For MultilineInput fields (complex JSON objects/arrays)
                    is_required = top_name in original_required
                    processed_inputs.append(
                        MultilineInput(
                            name=top_name,
                            display_name=top_schema.get("title") or top_name.replace("_", " ").title(),
                            info=(
                                top_schema.get("description") or "Provide JSON for this parameter (object or array)."
                            ),
                            required=is_required,  # Setting original schema
                        )
                    )

                return processed_inputs
            return result  # noqa: TRY300
        except ValueError as e:
            logger.warning(f"Error generating inputs for {action_key}: {e}")
            return []