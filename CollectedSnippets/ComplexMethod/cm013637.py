def make_partition(nodes: list[Node], module_type: type) -> SourcePartition:
        input_nodes = set()
        output_nodes = set()
        params = set()
        for node in nodes:
            for arg in node.args:
                if isinstance(arg, Node) and arg not in nodes and arg.op != "get_attr":
                    input_nodes.add(arg)

            if node.op == "get_attr":
                params.add(node)
                # get_attr nodes won't be output nodes
                continue

            for user in node.users:
                if user not in nodes:
                    output_nodes.add(node)

        return SourcePartition(
            nodes,
            module_type,
            list(input_nodes),
            list(output_nodes),
            list(params),  # type: ignore[arg-type]
        )