def fix_addtodictionary_blocks(self, agent: AgentDict) -> AgentDict:
        """
        Fix AddToDictionary blocks by removing empty CreateDictionaryBlock nodes
        that are linked to them.

        When an AddToDictionary block is found, this fixer:
        1. Checks if there's a CreateDictionaryBlock before it
        2. If CreateDictionaryBlock exists and is linked to AddToDictionary block,
           removes it and its link
        3. The AddToDictionary block will work with an empty dictionary as default

        Args:
            agent: The agent dictionary to fix

        Returns:
            The fixed agent dictionary
        """
        nodes = agent.get("nodes", [])
        links = agent.get("links", [])
        node_lookup = {node.get("id", ""): node for node in nodes}

        # First pass: identify CreateDictionaryBlock nodes linked to
        # AddToDictionary blocks
        create_dict_nodes_to_remove: set[str] = set()
        links_to_remove: list[dict[str, Any]] = []

        for link in links:
            source_node = node_lookup.get(link.get("source_id", ""))
            sink_node = node_lookup.get(link.get("sink_id", ""))

            if (
                source_node
                and sink_node
                and source_node.get("block_id") == _CREATE_DICT_BLOCK_ID
                and sink_node.get("block_id") == _ADDTODICTIONARY_BLOCK_ID
            ):
                create_dict_nodes_to_remove.add(source_node.get("id"))
                links_to_remove.append(link)
                self.add_fix_log(
                    f"Identified CreateDictionaryBlock "
                    f"{source_node.get('id')} linked to AddToDictionary "
                    f"block {sink_node.get('id')} for removal"
                )

        # Second pass: process nodes, skipping CreateDictionaryBlock nodes
        new_nodes = []
        for node in nodes:
            if node.get("id") in create_dict_nodes_to_remove:
                continue
            new_nodes.append(node)

        # Remove the links that were marked for removal
        new_links = [link for link in links if link not in links_to_remove]

        # Update the agent with new nodes and links
        agent["nodes"] = new_nodes
        agent["links"] = new_links

        return agent