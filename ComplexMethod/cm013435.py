def _from_dict(cls, d: dict[str, Any] | None) -> Optional["NodeSource"]:
        """
        Recursively deserialize from_node metadata from dictionary data.
        It is used to deserialize the from_node field from serialized metadata.
        Please use constructor NodeSource(node, ...) to create a NodeSource object.
        """
        if d is None:
            return None

        if not isinstance(d, dict):
            raise AssertionError(f"Expected a dict, got {type(d)}")

        # Create a NodeSource object directly without going through the constructor
        # to avoid issues with graph ID and node creation
        node_source = NodeSource.__new__(NodeSource)

        # Reset the cached properties
        node_source._action_string = None
        node_source._dict = None

        # Set the basic attributes
        node_source.pass_name = d.get("pass_name", "")

        # Parse action string back to NodeSourceAction enum list
        action_str = d.get("action", "")
        actions = []
        if action_str:
            for action_name in action_str.split("+"):
                if action_name.upper() == "CREATE":
                    actions.append(NodeSourceAction.CREATE)
                elif action_name.upper() == "REPLACE":
                    actions.append(NodeSourceAction.REPLACE)
        node_source.action = actions

        # Create the NodeInfo object directly
        if "name" in d and "target" in d and "graph_id" in d:
            node_info = NodeSource.NodeInfo(
                d.get("name", ""), d.get("target", ""), d.get("graph_id", -1)
            )
            node_source.node_info = node_info
        else:
            node_source.node_info = None

        # Recursively deserialize nested from_node
        if d.get("from_node", None) is not None:
            node_source.from_node = [
                result
                for fn in d.get("from_node", [])
                if (result := cls._from_dict(fn)) is not None
            ]
        else:
            node_source.from_node = []
        return node_source