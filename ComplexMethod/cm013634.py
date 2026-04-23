def _create_mock_node(
        self, name: str, op: str, target: Any = None, is_tensor: bool = True
    ) -> torch.fx.Node:
        """Helper to create a mock FX node with necessary attributes."""
        if op == "placeholder":
            node = self.graph.placeholder(name)
        elif op == "call_function":
            target = target or torch.add
            node = self.graph.call_function(target, args=())
        elif op == "call_module":
            target = target or "linear"
            node = self.graph.call_module(target)
        elif op == "call_method":
            target = target or "relu"
            node = self.graph.call_method(target)
        elif op == "output":
            node = self.graph.output(())
        else:
            node = self.graph.call_function(torch.add, args=())
            node.op = op

        node.name = name
        # Mock meta attribute for tensor type checking
        if is_tensor:
            node.meta = {"type": torch.Tensor}
        else:
            node.meta = {"type": int}  # Non-tensor type

        # Mock users dict (Node.users is dict[Node, None])
        users: dict[torch.fx.Node, None] = {}
        node.users = users

        # Initialize the _input_nodes dict (Node._input_nodes is dict[Node, None])
        input_nodes: dict[torch.fx.Node, None] = {}
        node._input_nodes = input_nodes

        return node