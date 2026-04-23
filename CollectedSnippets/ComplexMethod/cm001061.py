def fix_addtolist_blocks(self, agent: AgentDict) -> AgentDict:
        """
        Fix AddToList blocks by adding a prerequisite empty AddToList block.

        When an AddToList block is found, this fixer:
        1. Checks if there's a CreateListBlock before it (directly or through
           StoreValueBlock)
        2. If CreateListBlock exists (direct link), removes it and its link to
           AddToList block
        3. If CreateListBlock + StoreValueBlock exists, only removes the link from
           StoreValueBlock to AddToList block
        4. Adds an empty AddToList block before the original AddToList block
        5. The first block is standalone (not connected to other blocks)
        6. The second block receives input from previous blocks and can
           self-reference
        7. Ensures the original AddToList block has a self-referencing link
        8. Prevents duplicate prerequisite blocks by checking existing connections

        Args:
            agent: The agent dictionary to fix

        Returns:
            The fixed agent dictionary
        """
        nodes = agent.get("nodes", [])
        links = agent.get("links", [])
        node_lookup = {node.get("id", ""): node for node in nodes}
        new_nodes: list[dict[str, Any]] = []
        new_links: list[dict[str, Any]] = []
        original_addtolist_node_ids: set[str] = set()

        # First pass: identify CreateListBlock nodes and links to remove
        createlist_nodes_to_remove: set[str] = set()
        links_to_remove: list[dict[str, Any]] = []

        for link in links:
            source_node = node_lookup.get(link.get("source_id", ""))
            sink_node = node_lookup.get(link.get("sink_id", ""))

            # Case 1: CreateListBlock directly linked to AddToList block
            if (
                source_node
                and sink_node
                and source_node.get("block_id") == _CREATE_LIST_BLOCK_ID
                and sink_node.get("block_id") == _ADDTOLIST_BLOCK_ID
            ):
                createlist_nodes_to_remove.add(source_node.get("id"))
                links_to_remove.append(link)
                self.add_fix_log(
                    f"Identified CreateListBlock {source_node.get('id')} linked "
                    f"to AddToList block {sink_node.get('id')} for removal"
                )

            # Case 2: StoreValueBlock linked to AddToList block
            if (
                source_node
                and sink_node
                and source_node.get("block_id") == _STORE_VALUE_BLOCK_ID
                and sink_node.get("block_id") == _ADDTOLIST_BLOCK_ID
            ):
                storevalue_id = source_node.get("id")
                has_createlist_before = False
                for prev_link in links:
                    if prev_link.get("sink_id") == storevalue_id:
                        prev_source_node = node_lookup.get(
                            prev_link.get("source_id", "")
                        )
                        if (
                            prev_source_node
                            and prev_source_node.get("block_id")
                            == _CREATE_LIST_BLOCK_ID
                        ):
                            has_createlist_before = True
                            break

                if has_createlist_before:
                    links_to_remove.append(link)
                    self.add_fix_log(
                        f"Identified StoreValueBlock {storevalue_id} (with "
                        f"CreateListBlock before it) linked to AddToList block "
                        f"{sink_node.get('id')} - removing only the link"
                    )

        # Second pass: process nodes, skipping CreateListBlock nodes to remove
        prerequisite_counter = 0
        for node in nodes:
            if node.get("id") in createlist_nodes_to_remove:
                continue

            if node.get("block_id") == _ADDTOLIST_BLOCK_ID:
                original_addtolist_node_ids.add(node.get("id"))
                original_node_id = node.get("id")
                original_node_position = (node.get("metadata") or {}).get(
                    "position", {}
                )
                if original_node_position:
                    original_node_position_x = original_node_position.get("x", 0)
                    original_node_position_y = original_node_position.get("y", 0)
                else:
                    original_node_position_x = 0
                    original_node_position_y = 0

                # Check if there's already a prerequisite AddToList block
                has_prerequisite_block = False
                for link in links:
                    if (
                        link.get("sink_id") == original_node_id
                        and link.get("sink_name") == "list"
                        and link.get("source_name") == "updated_list"
                    ):
                        source_node = next(
                            (n for n in nodes if n.get("id") == link.get("source_id")),
                            None,
                        )
                        if (
                            source_node
                            and source_node.get("block_id") == _ADDTOLIST_BLOCK_ID
                            and source_node.get("id") != original_node_id
                        ):
                            has_prerequisite_block = True
                            break

                # Check if this node is already a prerequisite block
                is_prerequisite_block = (
                    node.get("input_default", {}).get("list") == []
                    and node.get("input_default", {}).get("entry") is None
                    and node.get("input_default", {}).get("entries") == []
                    and not any(
                        link.get("sink_id") == original_node_id
                        and link.get("sink_name") == "list"
                        for link in links
                    )
                )

                if is_prerequisite_block:
                    self.add_fix_log(
                        f"Skipped adding prerequisite AddToList block for "
                        f"{original_node_id} - this is already a prerequisite "
                        f"block"
                    )
                elif has_prerequisite_block:
                    self.add_fix_log(
                        f"Skipped adding prerequisite AddToList block for "
                        f"{original_node_id} - already has prerequisite block "
                        f"exists"
                    )
                else:
                    # Before adding prerequisite block, remove all links to
                    # the "list" input (except self-referencing)
                    links_to_list_input = []
                    for link in links:
                        if (
                            link.get("sink_id") == original_node_id
                            and link.get("sink_name") == "list"
                            and link.get("source_id") != original_node_id
                        ):
                            links_to_list_input.append(link)

                    for link in links_to_list_input:
                        if link not in links_to_remove:
                            links_to_remove.append(link)
                            self.add_fix_log(
                                f"Removed link from "
                                f"{link.get('source_id')}:"
                                f"{link.get('source_name')} to AddToList "
                                f"block {original_node_id} 'list' input "
                                f"(will be replaced by prerequisite block)"
                            )

                    prerequisite_node_id = generate_uuid()

                    prerequisite_node = {
                        "id": prerequisite_node_id,
                        "block_id": _ADDTOLIST_BLOCK_ID,
                        "input_default": {
                            "list": [],
                            "entry": None,
                            "entries": [],
                            "position": None,
                        },
                        "metadata": {
                            "position": {
                                "x": original_node_position_x - 800,
                                "y": original_node_position_y + 800,
                            }
                        },
                        "graph_id": agent.get("id"),
                        "graph_version": 1,
                    }
                    prerequisite_counter += 1

                    prerequisite_link = {
                        "id": generate_uuid(),
                        "source_id": prerequisite_node_id,
                        "source_name": "updated_list",
                        "sink_id": original_node_id,
                        "sink_name": "list",
                    }

                    new_nodes.append(prerequisite_node)
                    new_links.append(prerequisite_link)

                    self.add_fix_log(
                        f"Added prerequisite AddToList block "
                        f"{prerequisite_node_id} before {original_node_id}"
                    )

            # Add the original node
            new_nodes.append(node)

        # Add all existing links except those marked for removal
        new_links.extend([link for link in links if link not in links_to_remove])

        # Check for original AddToList blocks and ensure they have
        # self-referencing links
        for node in new_nodes:
            if (
                node.get("block_id") == _ADDTOLIST_BLOCK_ID
                and node.get("id") in original_addtolist_node_ids
            ):
                node_id = node.get("id")

                is_prerequisite_block = (
                    node.get("input_default", {}).get("list") == []
                    and node.get("input_default", {}).get("entry") is None
                    and node.get("input_default", {}).get("entries") == []
                    and not any(
                        link.get("sink_id") == node_id
                        and link.get("sink_name") == "list"
                        for link in new_links
                    )
                )

                if is_prerequisite_block:
                    self.add_fix_log(
                        f"Skipped adding self-referencing link for "
                        f"prerequisite AddToList block {node_id}"
                    )
                    continue

                has_self_reference = any(
                    link.get("source_id") == node_id
                    and link.get("sink_id") == node_id
                    and link.get("source_name") == "updated_list"
                    and link.get("sink_name") == "list"
                    for link in new_links
                )

                if not has_self_reference:
                    self_reference_link = {
                        "id": generate_uuid(),
                        "source_id": node_id,
                        "source_name": "updated_list",
                        "sink_id": node_id,
                        "sink_name": "list",
                    }
                    new_links.append(self_reference_link)
                    self.add_fix_log(
                        f"Added self-referencing link for original "
                        f"AddToList block {node_id}"
                    )

        # Update the agent with new nodes and links
        agent["nodes"] = new_nodes
        agent["links"] = new_links

        return agent