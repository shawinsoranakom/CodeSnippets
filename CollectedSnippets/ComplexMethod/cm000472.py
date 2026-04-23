def _validate_graph_get_errors(
        graph: BaseGraph,
        for_run: bool = False,
        nodes_input_masks: Optional["NodesInputMasks"] = None,
    ) -> dict[str, dict[str, str]]:
        """
        Validate graph and return structured errors per node.

        Returns: dict[node_id, dict[field_name, error_message]]
        """
        # First, check for structural issues with the graph
        try:
            GraphModel._validate_graph_structure(graph)
        except ValueError:
            # If structural validation fails, we can't provide per-node errors
            # so we re-raise as is
            raise

        # Collect errors per node
        node_errors: dict[str, dict[str, str]] = defaultdict(dict)

        # Validate tool orchestrator nodes
        nodes_block = {
            node.id: block
            for node in graph.nodes
            if (block := get_block(node.block_id)) is not None
        }

        input_links: dict[str, list[Link]] = defaultdict(list)

        for link in graph.links:
            input_links[link.sink_id].append(link)

        # Nodes: required fields are filled or connected and dependencies are satisfied
        for node in graph.nodes:
            if (block := nodes_block.get(node.id)) is None:
                # For invalid blocks, we still raise immediately as this is a structural issue
                raise ValueError(f"Invalid block {node.block_id} for node #{node.id}")

            if block.disabled:
                raise ValueError(
                    f"Block {node.block_id} is disabled and cannot be used in graphs"
                )

            node_input_mask = (
                nodes_input_masks.get(node.id, {}) if nodes_input_masks else {}
            )
            provided_inputs = set(
                [sanitize_pin_name(name) for name in node.input_default]
                + [
                    sanitize_pin_name(link.sink_name)
                    for link in input_links.get(node.id, [])
                ]
                + ([name for name in node_input_mask] if node_input_mask else [])
            )
            InputSchema = block.input_schema

            for name in (required_fields := InputSchema.get_required_fields()):
                if (
                    name not in provided_inputs
                    # Checking availability of credentials is done by ExecutionManager
                    and name not in InputSchema.get_credentials_fields()
                    # Validate only I/O nodes, or validate everything when executing
                    and (
                        for_run
                        or block.block_type
                        in [
                            BlockType.INPUT,
                            BlockType.OUTPUT,
                            BlockType.AGENT,
                        ]
                    )
                ):
                    node_errors[node.id][name] = "This field is required"

                if (
                    block.block_type == BlockType.INPUT
                    and (input_key := node.input_default.get("name"))
                    and is_credentials_field_name(input_key)
                ):
                    node_errors[node.id]["name"] = (
                        f"'{input_key}' is a reserved input name: "
                        "'credentials' and `*_credentials` are reserved"
                    )

            # Check custom block-level validation (e.g., MCP dynamic tool arguments).
            # Blocks can override get_missing_input to report additional missing fields
            # beyond the standard top-level required fields.
            if for_run:
                credential_fields = InputSchema.get_credentials_fields()
                custom_missing = InputSchema.get_missing_input(node.input_default)
                for field_name in custom_missing:
                    if (
                        field_name not in provided_inputs
                        and field_name not in credential_fields
                    ):
                        node_errors[node.id][field_name] = "This field is required"

            # Get input schema properties and check dependencies
            input_fields = InputSchema.model_fields

            def has_value(node: Node, name: str):
                return (
                    (
                        name in node.input_default
                        and node.input_default[name] is not None
                        and str(node.input_default[name]).strip() != ""
                    )
                    or (name in input_fields and input_fields[name].default is not None)
                    or (
                        name in node_input_mask
                        and node_input_mask[name] is not None
                        and str(node_input_mask[name]).strip() != ""
                    )
                )

            # Validate dependencies between fields
            for field_name in input_fields.keys():
                field_json_schema = InputSchema.get_field_schema(field_name)

                dependencies: list[str] = []

                # Check regular field dependencies (only pre graph execution)
                if for_run:
                    dependencies.extend(field_json_schema.get("depends_on", []))

                # Require presence of credentials discriminator (always).
                # The `discriminator` is either the name of a sibling field (str),
                # or an object that discriminates between possible types for this field:
                # {"propertyName": prop_name, "mapping": {prop_value: sub_schema}}
                if (
                    discriminator := field_json_schema.get("discriminator")
                ) and isinstance(discriminator, str):
                    dependencies.append(discriminator)

                if not dependencies:
                    continue

                # Check if dependent field has value in input_default
                field_has_value = has_value(node, field_name)
                field_is_required = field_name in required_fields

                # Check for missing dependencies when dependent field is present
                missing_deps = [dep for dep in dependencies if not has_value(node, dep)]
                if missing_deps and (field_has_value or field_is_required):
                    node_errors[node.id][
                        field_name
                    ] = f"Requires {', '.join(missing_deps)} to be set"

        return node_errors