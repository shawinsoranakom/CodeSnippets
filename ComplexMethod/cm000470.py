def aggregate_credentials_inputs(
        self,
    ) -> dict[str, tuple[CredentialsFieldInfo, set[tuple[str, str]], bool]]:
        """
        Returns:
            dict[aggregated_field_key, tuple(
                CredentialsFieldInfo: A spec for one aggregated credentials field
                    (now includes discriminator_values from matching nodes)
                set[(node_id, field_name)]: Node credentials fields that are
                    compatible with this aggregated field spec
                bool: True if the field is required (any node has credentials_optional=False)
            )]
        """
        # First collect all credential field data with input defaults
        # Track (field_info, (node_id, field_name), is_required) for each credential field
        node_credential_data: list[tuple[CredentialsFieldInfo, tuple[str, str]]] = []
        node_required_map: dict[str, bool] = {}  # node_id -> is_required

        for graph in [self] + self.sub_graphs:
            for node in graph.nodes:
                # A node's credentials are optional if either:
                # 1. The node metadata says so (credentials_optional=True), or
                # 2. All credential fields on the block have defaults (not required by schema)
                block_required = node.block.input_schema.get_required_fields()
                creds_required_by_schema = any(
                    fname in block_required
                    for fname in node.block.input_schema.get_credentials_fields()
                )
                node_required_map[node.id] = (
                    not node.credentials_optional and creds_required_by_schema
                )

                for (
                    field_name,
                    field_info,
                ) in node.block.input_schema.get_credentials_fields_info().items():
                    discriminator = field_info.discriminator
                    if not discriminator:
                        node_credential_data.append((field_info, (node.id, field_name)))
                        continue

                    discriminator_value = node.input_default.get(discriminator)
                    if discriminator_value is None:
                        node_credential_data.append((field_info, (node.id, field_name)))
                        continue

                    discriminated_info = field_info.discriminate(discriminator_value)
                    discriminated_info.discriminator_values.add(discriminator_value)

                    node_credential_data.append(
                        (discriminated_info, (node.id, field_name))
                    )

        # Combine credential field info (this will merge discriminator_values automatically)
        combined = CredentialsFieldInfo.combine(*node_credential_data)

        # Add is_required flag to each aggregated field
        # A field is required if ANY node using it has credentials_optional=False
        return {
            key: (
                field_info,
                node_field_pairs,
                any(
                    node_required_map.get(node_id, True)
                    for node_id, _ in node_field_pairs
                ),
            )
            for key, (field_info, node_field_pairs) in combined.items()
        }