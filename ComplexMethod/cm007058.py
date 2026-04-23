def get_dynamic_values(self) -> dict[str, Any]:
        """Extract simple values from all dynamic inputs, handling both manual and connected inputs."""
        dynamic_values = {}
        connection_info = {}
        form_fields = getattr(self, "form_fields", [])

        for field_config in form_fields:
            # Safety check to ensure field_config is not None
            if field_config is None:
                continue

            field_name = field_config.get("field_name", "")
            if field_name:
                dynamic_input_name = f"dynamic_{field_name}"
                value = getattr(self, dynamic_input_name, None)

                # Extract simple values from connections or manual input
                if value is not None:
                    try:
                        extracted_value = self._extract_simple_value(value)
                        dynamic_values[field_name] = extracted_value

                        # Determine connection type for status
                        if hasattr(value, "text") and hasattr(value, "timestamp"):
                            connection_info[field_name] = "Connected (Message)"
                        elif hasattr(value, "data"):
                            connection_info[field_name] = "Connected (Data)"
                        elif isinstance(value, (str, int, float, bool, list, dict)):
                            connection_info[field_name] = "Manual input"
                        else:
                            connection_info[field_name] = "Connected (Object)"

                    except (AttributeError, TypeError, ValueError):
                        # Fallback to string representation if all else fails
                        dynamic_values[field_name] = str(value)
                        connection_info[field_name] = "Error"
                else:
                    # Use empty default value if nothing connected
                    dynamic_values[field_name] = ""
                    connection_info[field_name] = "Empty default"

        # Store connection info for status output
        self._connection_info = connection_info
        return dynamic_values