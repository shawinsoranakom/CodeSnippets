def fix_storevalue_before_condition(self, agent: AgentDict) -> AgentDict:
        """
        Add a StoreValueBlock before each ConditionBlock to provide a value for 'value2'.

        - Creates a StoreValueBlock node with default input and data False
        - Adds a link from the StoreValueBlock 'output' to the ConditionBlock 'value2'
        - Skips if a link to 'value2' already exists for the ConditionBlock
        - Prevents duplicate StoreValueBlocks by checking if one already exists for the
          same condition

        Args:
            agent: The agent dictionary to fix

        Returns:
            The fixed agent dictionary
        """

        nodes = agent.get("nodes", [])
        links = agent.get("links", []) or []

        # Collect ConditionBlock node ids
        condition_block_id = _FIX_VALUE2_EMPTY_STRING_BLOCK_IDS[0]
        condition_node_ids = {
            node.get("id")
            for node in nodes
            if node.get("block_id") == condition_block_id
        }

        if not condition_node_ids:
            return agent

        new_links = []
        nodes_to_add = []
        store_node_counter = 0  # Counter to ensure unique positions

        for link in links:
            # Identify links going into ConditionBlock.value2
            if (
                link.get("sink_id") in condition_node_ids
                and link.get("sink_name") == "value2"
            ):
                condition_node_id = link.get("sink_id")

                # If the upstream source is already a StoreValueBlock.output, keep as-is
                source_node = next(
                    (n for n in nodes if n.get("id") == link.get("source_id")),
                    None,
                )
                if (
                    source_node
                    and source_node.get("block_id") == _STORE_VALUE_BLOCK_ID
                    and link.get("source_name") == "output"
                ):
                    new_links.append(link)
                    continue

                # Check if there's already a StoreValueBlock connected to this
                # condition's value2. This prevents duplicates when the fix runs
                # multiple times.
                existing_storevalue_for_condition = False
                for existing_link in links:
                    if (
                        existing_link.get("sink_id") == condition_node_id
                        and existing_link.get("sink_name") == "value2"
                    ):
                        existing_source_node = next(
                            (
                                n
                                for n in nodes
                                if n.get("id") == existing_link.get("source_id")
                            ),
                            None,
                        )
                        if (
                            existing_source_node
                            and existing_source_node.get("block_id")
                            == _STORE_VALUE_BLOCK_ID
                            and existing_link.get("source_name") == "output"
                        ):
                            existing_storevalue_for_condition = True
                            break

                if existing_storevalue_for_condition:
                    self.add_fix_log(
                        f"Skipped adding StoreValueBlock for ConditionBlock "
                        f"{condition_node_id} - already has one connected"
                    )
                    new_links.append(link)
                    continue

                # Create StoreValueBlock node (input will be linked; data left
                # default None)
                store_node_id = generate_uuid()
                store_node = {
                    "id": store_node_id,
                    "block_id": _STORE_VALUE_BLOCK_ID,
                    "input_default": {"data": None},
                    "metadata": {
                        "position": {
                            "x": store_node_counter * 200,
                            "y": -100,
                        }
                    },
                    "graph_id": agent.get("id"),
                    "graph_version": 1,
                }
                nodes_to_add.append(store_node)
                store_node_counter += 1

                # Rewire: old source -> StoreValueBlock.input
                upstream_to_store_link = {
                    "id": generate_uuid(),
                    "source_id": link.get("source_id"),
                    "source_name": link.get("source_name"),
                    "sink_id": store_node_id,
                    "sink_name": "input",
                }

                # Then StoreValueBlock.output -> ConditionBlock.value2
                store_to_condition_link = {
                    "id": generate_uuid(),
                    "source_id": store_node_id,
                    "source_name": "output",
                    "sink_id": condition_node_id,
                    "sink_name": "value2",
                }

                new_links.append(upstream_to_store_link)
                new_links.append(store_to_condition_link)

                self.add_fix_log(
                    f"Inserted StoreValueBlock {store_node_id} between "
                    f"{link.get('source_id')}:{link.get('source_name')} and "
                    f"ConditionBlock {condition_node_id} value2"
                )
            else:
                new_links.append(link)

        if nodes_to_add:
            nodes.extend(nodes_to_add)
            agent["nodes"] = nodes
            agent["links"] = new_links

        return agent