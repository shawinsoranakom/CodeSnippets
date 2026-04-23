def combine(
        cls, *fields: tuple[CredentialsFieldInfo[CP, CT], T]
    ) -> dict[str, tuple[CredentialsFieldInfo[CP, CT], set[T]]]:
        """
        Combines multiple CredentialsFieldInfo objects into as few as possible.

        Rules:
        - Items can only be combined if they have the same supported credentials types
          and the same supported providers.
        - When combining items, the `required_scopes` of the result is a join
          of the `required_scopes` of the original items.

        Params:
            *fields: (CredentialsFieldInfo, key) objects to group and combine

        Returns:
            A sequence of tuples containing combined CredentialsFieldInfo objects and
            the set of keys of the respective original items that were grouped together.
        """
        if not fields:
            return {}

        # Group fields by their provider and supported_types
        # For HTTP host-scoped credentials, also group by host
        grouped_fields: defaultdict[
            tuple[frozenset[CP], frozenset[CT]],
            list[tuple[T, CredentialsFieldInfo[CP, CT]]],
        ] = defaultdict(list)

        for field, key in fields:
            if (
                field.discriminator
                and not field.discriminator_mapping
                and field.discriminator_values
            ):
                # URL-based discrimination (e.g. HTTP host-scoped, MCP server URL):
                # Each unique host gets its own credential entry.
                provider_prefix = next(iter(field.provider))
                # Use .value for enum types to get the plain string (e.g. "mcp" not "ProviderName.MCP")
                prefix_str = getattr(provider_prefix, "value", str(provider_prefix))
                providers = frozenset(
                    [cast(CP, prefix_str)]
                    + [
                        cast(CP, parse_url(str(value)).netloc)
                        for value in field.discriminator_values
                    ]
                )
            else:
                providers = frozenset(field.provider)

            group_key = (providers, frozenset(field.supported_types))
            grouped_fields[group_key].append((key, field))

        # Combine fields within each group
        result: dict[str, tuple[CredentialsFieldInfo[CP, CT], set[T]]] = {}

        for key, group in grouped_fields.items():
            # Start with the first field in the group
            _, combined = group[0]

            # Track the keys that were combined
            combined_keys = {key for key, _ in group}

            # Combine required_scopes from all fields in the group
            all_scopes = set()
            for _, field in group:
                if field.required_scopes:
                    all_scopes.update(field.required_scopes)

            # Combine discriminator_values from all fields in the group (removing duplicates)
            all_discriminator_values = []
            for _, field in group:
                for value in field.discriminator_values:
                    if value not in all_discriminator_values:
                        all_discriminator_values.append(value)

            # Generate the key for the combined result
            providers_key, supported_types_key = key
            group_key = (
                "-".join(sorted(providers_key))
                + "_"
                + "-".join(sorted(supported_types_key))
                + "_credentials"
            )

            result[group_key] = (
                CredentialsFieldInfo[CP, CT](
                    credentials_provider=combined.provider,
                    credentials_types=combined.supported_types,
                    credentials_scopes=frozenset(all_scopes) or None,
                    discriminator=combined.discriminator,
                    discriminator_mapping=combined.discriminator_mapping,
                    discriminator_values=set(all_discriminator_values),
                ),
                combined_keys,
            )

        return result