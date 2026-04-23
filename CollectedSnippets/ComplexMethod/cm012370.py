def build_subgraph(self, chunk_size: int) -> GraphModule:
        """
        Build a subgraph for the given chunk size.
        The last chunk can be smaller and a new subgraph will be created
        to avoid involving dynamic shapes.
        """
        new_graph = Graph()
        env: dict[Node, Node] = {}

        def _create_placeholder_node(input_node: Node) -> Node:
            new_node = new_graph.placeholder(input_node.name)
            fake_tensor = input_node.meta["val"]
            chunking_meta = get_chunking_meta(input_node)
            if chunking_meta is not None and chunking_meta.chunk_dim is not None:
                # the node is chunked and we need update the
                # fake tensor
                # TODO any better way to do this?
                new_tensor = aten.slice.Tensor(
                    fake_tensor, chunking_meta.chunk_dim, 0, chunk_size
                )
                fake_tensor = new_tensor
            new_node.meta = {"val": fake_tensor}
            return new_node

        for node_idx, input_node in enumerate(self.subgraph_input):
            env[input_node] = _create_placeholder_node(input_node)

        for overriden_tangent_node in self.overriden_tangent.values():
            assert overriden_tangent_node is not None
            env[overriden_tangent_node] = _create_placeholder_node(
                overriden_tangent_node
            )

        for accum in self.accumulators.values():
            assert accum is not None
            env[accum] = _create_placeholder_node(accum)

        for original_node in self.subgraph_body + self.subgraph_output:
            assert original_node.op != "placeholder"

            # Chunk aten.full
            if (
                original_node.target == aten.full.default
                and (meta := get_chunking_meta(original_node)) is not None
                and meta.chunk_dim is not None
            ):
                shape = list(original_node.args[0])  # type: ignore[arg-type]
                # pyrefly: ignore [unsupported-operation]
                shape[meta.chunk_dim] = chunk_size
                env[original_node] = new_graph.call_function(
                    aten.full.default,
                    (shape, original_node.args[1]),
                    original_node.kwargs,
                )
                continue
            # Chunk aten.expand: adjust the target shape at the chunk dimension
            if (
                original_node.target == aten.expand.default
                and isinstance(original_node.args[0], torch.fx.Node)
                and (meta := get_chunking_meta(original_node)) is not None
                and meta.chunk_dim is not None
            ):
                shape = list(original_node.args[1])  # type: ignore[arg-type]
                # pyrefly: ignore [unsupported-operation]
                shape[meta.chunk_dim] = chunk_size
                env[original_node] = new_graph.call_function(
                    aten.expand.default,
                    (env.get(original_node.args[0], original_node.args[0]), shape),  # type: ignore[arg-type]
                    original_node.kwargs,
                )
                continue

            # Chunk aten.view: adjust the target shape at the chunk dimension
            if (
                original_node.target == aten.view.default
                and isinstance(original_node.args[0], torch.fx.Node)
                and (meta := get_chunking_meta(original_node)) is not None
                and meta.chunk_dim is not None
            ):
                shape = list(original_node.args[1])  # type: ignore[arg-type]
                # pyrefly: ignore [unsupported-operation]
                shape[meta.chunk_dim] = chunk_size
                env[original_node] = new_graph.call_function(
                    aten.view.default,
                    (env[original_node.args[0]], shape),  # type: ignore[arg-type]
                    original_node.kwargs,
                )
                continue

            # create the node with chunked inputs
            env[original_node] = new_graph.node_copy(original_node, lambda x: env[x])

        # Do the accumulation inside this subgraph
        for node, accum in self.accumulators.items():
            lhs = env[node]
            assert accum is not None
            rhs = env[accum]

            # add `addend` and `accum`
            add_out = new_graph.call_function(aten.add.Tensor, (lhs, rhs))

            # override the chunk value
            env[node] = add_out

        out_values = []
        for node in self.subgraph_output:
            out_values.append(env[node])

        new_graph.output(tuple(out_values))
        new_graph.eliminate_dead_code()
        new_graph.lint()

        sub_gm = torch.fx._lazy_graph_module._make_graph_module(self.gm, new_graph)
        fake_tensor_prop(sub_gm)
        return sub_gm