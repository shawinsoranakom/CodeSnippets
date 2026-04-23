def validate_link_node_references(self, agent: AgentDict) -> bool:
        """
        Validate that all node IDs referenced in links actually exist in the
        agent's nodes. Returns True if all link references are valid, False
        otherwise.
        """
        valid = True

        # Create a set of all valid node IDs for fast lookup
        valid_node_ids = {
            node.get("id") for node in agent.get("nodes", []) if node.get("id")
        }

        # Check each link's source_id and sink_id
        for link in agent.get("links", []):
            link_id = link.get("id", "Unknown")
            source_id = link.get("source_id")
            sink_id = link.get("sink_id")
            source_name = link.get("source_name", "")
            sink_name = link.get("sink_name", "")

            # Check source_id
            if not source_id:
                self.add_error(
                    f"Link '{link_id}' is missing a 'source_id' field. "
                    f"Every link must reference a valid source node."
                )
                valid = False
            elif source_id not in valid_node_ids:
                self.add_error(
                    f"Link '{link_id}' references source_id '{source_id}' "
                    f"which does not exist in the agent's nodes. The link "
                    f"from '{source_name}' cannot be established because "
                    f"the source node is missing."
                )
                valid = False

            # Check sink_id
            if not sink_id:
                self.add_error(
                    f"Link '{link_id}' is missing a 'sink_id' field. "
                    f"Every link must reference a valid sink (destination) "
                    f"node."
                )
                valid = False
            elif sink_id not in valid_node_ids:
                self.add_error(
                    f"Link '{link_id}' references sink_id '{sink_id}' "
                    f"which does not exist in the agent's nodes. The link "
                    f"to '{sink_name}' cannot be established because the "
                    f"destination node is missing."
                )
                valid = False

        return valid