def _resolve_discriminated_credentials(
    block: AnyBlockSchema,
    input_data: dict[str, Any],
) -> dict[str, CredentialsFieldInfo]:
    """Resolve credential requirements, applying discriminator logic where needed.

    Handles two discrimination modes:
    1. **Provider-based** (``discriminator_mapping`` is set): the discriminator
       field value selects the provider (e.g. an AI model name -> provider).
    2. **URL/host-based** (``discriminator`` is set but ``discriminator_mapping``
       is ``None``): the discriminator field value (typically a URL) is added to
       ``discriminator_values`` so that host-scoped credential matching can
       compare the credential's host against the target URL.
    """
    credentials_fields_info = block.input_schema.get_credentials_fields_info()
    if not credentials_fields_info:
        return {}

    resolved: dict[str, CredentialsFieldInfo] = {}

    for field_name, field_info in credentials_fields_info.items():
        effective_field_info = field_info

        if field_info.discriminator:
            discriminator_value = input_data.get(field_info.discriminator)
            if discriminator_value is None:
                field = block.input_schema.model_fields.get(field_info.discriminator)
                if field and field.default is not PydanticUndefined:
                    discriminator_value = field.default

            if discriminator_value is not None:
                if field_info.discriminator_mapping:
                    # Provider-based discrimination (e.g. model -> provider)
                    if discriminator_value in field_info.discriminator_mapping:
                        effective_field_info = field_info.discriminate(
                            discriminator_value
                        )
                        effective_field_info.discriminator_values.add(
                            discriminator_value
                        )
                        # Model names are safe to log (not PII); URLs are
                        # intentionally omitted in the host-based branch below.
                        logger.debug(
                            "Discriminated provider for %s: %s -> %s",
                            field_name,
                            discriminator_value,
                            effective_field_info.provider,
                        )
                else:
                    # URL/host-based discrimination (e.g. url -> host matching).
                    # Deep copy to avoid mutating the cached schema-level
                    # field_info (model_copy() is shallow — the mutable set
                    # would be shared).
                    effective_field_info = field_info.model_copy(deep=True)
                    effective_field_info.discriminator_values.add(discriminator_value)
                    logger.debug(
                        "Added discriminator value for host matching on %s",
                        field_name,
                    )

        resolved[field_name] = effective_field_info

    return resolved