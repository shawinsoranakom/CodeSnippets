def fix_addtolist_gmail_self_reference(self, agent: AgentDict) -> AgentDict:
        """
        Remove self-referencing links from AddToList blocks that are connected
        to GmailSendBlock.

        When an AddToList block has a link to a GmailSendBlock, this fixer:
        1. Identifies the AddToList block that is linked to a GmailSendBlock
        2. Removes the self-referencing link (updated_list -> list) from that
           AddToList block

        Args:
            agent: The agent dictionary to fix

        Returns:
            The fixed agent dictionary
        """
        nodes = agent.get("nodes", [])
        links = agent.get("links", [])

        # Find AddToList blocks that are connected to GmailSendBlock
        addtolist_nodes_linked_to_gmail: set[str] = set()

        for link in links:
            source_node = next(
                (node for node in nodes if node.get("id") == link.get("source_id")),
                None,
            )
            sink_node = next(
                (node for node in nodes if node.get("id") == link.get("sink_id")),
                None,
            )

            if (
                source_node
                and sink_node
                and source_node.get("block_id") == _ADDTOLIST_BLOCK_ID
                and sink_node.get("block_id") == _GMAIL_SEND_BLOCK_ID
            ):
                addtolist_nodes_linked_to_gmail.add(source_node.get("id"))
                self.add_fix_log(
                    f"Identified AddToList block {source_node.get('id')} "
                    f"linked to GmailSendBlock {sink_node.get('id')}"
                )

        # Remove self-referencing links from identified AddToList blocks
        if addtolist_nodes_linked_to_gmail:
            links_to_remove = []

            for link in links:
                if (
                    link.get("source_id") in addtolist_nodes_linked_to_gmail
                    and link.get("sink_id") in addtolist_nodes_linked_to_gmail
                    and link.get("source_id") == link.get("sink_id")
                    and link.get("source_name") == "updated_list"
                    and link.get("sink_name") == "list"
                ):
                    links_to_remove.append(link)
                    self.add_fix_log(
                        f"Removed self-referencing link {link.get('id')} "
                        f"from AddToList block {link.get('source_id')} "
                        f"(linked to GmailSendBlock)"
                    )

            if links_to_remove:
                agent["links"] = [link for link in links if link not in links_to_remove]

        return agent