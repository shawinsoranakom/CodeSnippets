def credentials_input_schema(self) -> dict[str, Any]:
        graph_credentials_inputs = self.aggregate_credentials_inputs()

        logger.debug(
            f"Combined credentials input fields for graph #{self.id} ({self.name}): "
            f"{graph_credentials_inputs}"
        )

        # Warn if same-provider credentials inputs can't be combined (= bad UX)
        graph_cred_fields = list(graph_credentials_inputs.values())
        for i, (field, keys, _) in enumerate(graph_cred_fields):
            for other_field, other_keys, _ in list(graph_cred_fields)[i + 1 :]:
                if field.provider != other_field.provider:
                    continue
                if ProviderName.HTTP in field.provider:
                    continue
                # MCP credentials are intentionally split by server URL
                if ProviderName.MCP in field.provider:
                    continue

                # If this happens, that means a block implementation probably needs
                # to be updated.
                logger.warning(
                    "Multiple combined credentials fields "
                    f"for provider {field.provider} "
                    f"on graph #{self.id} ({self.name}); "
                    f"fields: {field} <> {other_field};"
                    f"keys: {keys} <> {other_keys}."
                )

        # Build JSON schema directly to avoid expensive create_model + validation overhead
        properties = {}
        required_fields = []

        for agg_field_key, (
            field_info,
            _,
            is_required,
        ) in graph_credentials_inputs.items():
            providers = list(field_info.provider)
            cred_types = list(field_info.supported_types)

            field_schema: dict[str, Any] = {
                "credentials_provider": providers,
                "credentials_types": cred_types,
                "type": "object",
                "properties": {
                    "id": {"title": "Id", "type": "string"},
                    "title": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "default": None,
                        "title": "Title",
                    },
                    "provider": {
                        "title": "Provider",
                        "type": "string",
                        **(
                            {"enum": providers}
                            if len(providers) > 1
                            else {"const": providers[0]}
                        ),
                    },
                    "type": {
                        "title": "Type",
                        "type": "string",
                        **(
                            {"enum": cred_types}
                            if len(cred_types) > 1
                            else {"const": cred_types[0]}
                        ),
                    },
                },
                "required": ["id", "provider", "type"],
            }

            # Add a descriptive display title when URL-based discriminator values
            # are present (e.g. "mcp.sentry.dev" instead of just "Mcp")
            if (
                field_info.discriminator
                and not field_info.discriminator_mapping
                and field_info.discriminator_values
            ):
                hostnames = sorted(
                    parse_url(str(v)).netloc for v in field_info.discriminator_values
                )
                field_schema["display_name"] = ", ".join(hostnames)

            # Add other (optional) field info items
            field_schema.update(
                field_info.model_dump(
                    by_alias=True,
                    exclude_defaults=True,
                    exclude={"provider", "supported_types"},  # already included above
                )
            )

            # Ensure field schema is well-formed
            CredentialsMetaInput.validate_credentials_field_schema(
                field_schema, agg_field_key
            )

            properties[agg_field_key] = field_schema
            if is_required:
                required_fields.append(agg_field_key)

        return {
            "type": "object",
            "properties": properties,
            "required": required_fields,
        }