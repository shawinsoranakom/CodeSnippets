def test_resnet50(self):
        gm_run = symbolic_trace(resnet50())
        sample_input = torch.randn(1, 3, 224, 224)

        # run our nodes
        ShapeProp(gm_run).propagate(sample_input)

        gm_static = symbolic_trace(resnet50())

        for n in gm_static.graph.nodes:
            n.type = None

        g = GraphTypeChecker({}, gm_static)
        g.type_check()
        gm_static.graph.eliminate_dead_code()
        gm_run.graph.eliminate_dead_code()
        # here we are checking for consistency with fully dynamic nodes
        for n1, n2 in zip(gm_static.graph.nodes, gm_run.graph.nodes):
            if not is_consistent(n1.type, TensorType(n2.meta["tensor_meta"].shape)):
                raise AssertionError(
                    f"Expected n1.type consistent with "
                    f"TensorType({n2.meta['tensor_meta'].shape})"
                )

        # here we give the same input as to runtime
        gm_static_with_types = symbolic_trace(resnet50())

        # we initialize our placeholder
        for n in gm_static_with_types.graph.nodes:
            if n.op == "placeholder":
                n.type = TensorType((1, 3, 224, 224))

        g = GraphTypeChecker({}, gm_static_with_types)
        g.type_check()
        for n1, n2 in zip(gm_static_with_types.graph.nodes, gm_run.graph.nodes):
            expected_type = TensorType(n2.meta["tensor_meta"].shape)
            if n1.type != expected_type:
                raise AssertionError(
                    f"Expected n1.type == {expected_type}, got {n1.type}"
                )

        # apply shape inference to graph and check
        # that the batch size is equal across all layers
        infer_symbolic_types(gm_static)

        batch_sizes = set()
        gm_static.graph.eliminate_dead_code()
        for n in gm_static.graph.nodes:
            if not isinstance(n.type, TensorType):
                raise AssertionError(
                    f"Expected n.type to be TensorType, got {type(n.type)}"
                )
            batch_sizes.add(n.type.__args__[0])
        if len(batch_sizes) != 1:
            raise AssertionError(
                f"Expected len(batch_sizes) == 1, got {len(batch_sizes)}"
            )