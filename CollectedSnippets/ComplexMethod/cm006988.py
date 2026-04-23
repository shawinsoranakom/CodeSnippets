def update_build_config(self, build_config: dotdict, field_value: Any, field_name: str | None = None) -> dotdict:
        """Update the template field type based on the selected mode."""
        if field_name == "use_double_brackets":
            # Change the template field type based on mode
            is_mustache = field_value is True
            if is_mustache:
                build_config["template"]["type"] = FieldTypes.MUSTACHE_PROMPT.value
            else:
                build_config["template"]["type"] = FieldTypes.PROMPT.value

            # Re-process the template to update variables when mode changes
            template_value = build_config.get("template", {}).get("value", "")
            if template_value:
                # Ensure custom_fields is properly initialized
                if "custom_fields" not in build_config:
                    build_config["custom_fields"] = {}

                # Clean up fields from the OLD mode before processing with NEW mode
                # This ensures we don't keep fields with wrong syntax even if validation fails
                old_custom_fields = build_config["custom_fields"].get("template", [])
                for old_field in list(old_custom_fields):
                    # Remove the field from custom_fields and template
                    if old_field in old_custom_fields:
                        old_custom_fields.remove(old_field)
                    build_config.pop(old_field, None)

                # Try to process template with new mode to add new variables
                # If validation fails, at least we cleaned up old fields
                try:
                    # Validate mustache templates for security
                    if is_mustache:
                        validate_mustache_template(template_value)

                    # Re-process template with new mode to add new variables
                    _ = process_prompt_template(
                        template=template_value,
                        name="template",
                        custom_fields=build_config["custom_fields"],
                        frontend_node_template=build_config,
                        is_mustache=is_mustache,
                    )
                except ValueError as e:
                    # If validation fails, we still updated the mode and cleaned old fields
                    # User will see error when they try to save
                    logger.debug(f"Template validation failed during mode switch: {e}")
        return build_config