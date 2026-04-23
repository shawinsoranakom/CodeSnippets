def fix_data_sampling_sample_size(self, agent: AgentDict) -> AgentDict:
        """
        Fix DataSamplingBlock by setting sample_size to 1 as default.
        If old value is set as default, just reset to 1.
        If old value is from another block, delete that link and set 1 as default.

        Args:
            agent: The agent dictionary to fix

        Returns:
            The fixed agent dictionary
        """

        nodes = agent.get("nodes", [])
        links = agent.get("links", [])
        links_to_remove: list[dict[str, Any]] = []

        for node in nodes:
            if node.get("block_id") == _DATA_SAMPLING_BLOCK_ID:
                node_id = node.get("id")
                input_default = node.get("input_default", {})

                # Check if there's a link to the sample_size field
                has_sample_size_link = False
                for link in links:
                    if (
                        link.get("sink_id") == node_id
                        and link.get("sink_name") == "sample_size"
                    ):
                        has_sample_size_link = True
                        links_to_remove.append(link)
                        self.add_fix_log(
                            f"Removed link {link.get('id')} to "
                            f"DataSamplingBlock {node_id} sample_size "
                            f"field (will set default to 1)"
                        )

                # Set sample_size to 1 as default
                old_value = input_default.get("sample_size", None)
                input_default["sample_size"] = 1

                if has_sample_size_link:
                    self.add_fix_log(
                        f"Fixed DataSamplingBlock {node_id} sample_size: "
                        f"removed link and set default to 1"
                    )
                elif old_value != 1:
                    self.add_fix_log(
                        f"Fixed DataSamplingBlock {node_id} sample_size: "
                        f"{old_value} -> 1"
                    )

        # Remove the links that were marked for removal
        if links_to_remove:
            agent["links"] = [link for link in links if link not in links_to_remove]

        return agent