def test_data_type_propogation(self):
        from torch._dynamo.utils import detect_fake_mode
        from torch._inductor.codegen.common import boolean_ops
        from torch._inductor.compile_fx import shape_env_from_inputs
        from torch._inductor.debug import DebugContext
        from torch._inductor.decomposition import decompositions
        from torch._inductor.graph import GraphLowering
        from torch._inductor.virtualized import V
        from torch.fx.passes.fake_tensor_prop import FakeTensorProp

        def get_data_type(node: torch.fx.Node):
            if OptimizationContext.key in node.meta:
                return node.meta[OptimizationContext.key].dtype
            else:
                return None

        def func(arg0_1):
            max_pool2d_with_indices = torch.ops.aten.max_pool2d_with_indices.default(
                arg0_1, [3, 3], [2, 2], [1, 1]
            )
            arg0_1 = None
            getitem = max_pool2d_with_indices[0]
            max_pool2d_with_indices = None
            return (getitem,)

        example_inputs = [
            torch.randn(10, 32, 20, 20, dtype=torch.bfloat16).to(
                memory_format=torch.channels_last
            )
        ]

        gm = make_fx(func, decomposition_table=decompositions, tracing_mode="fake")(
            *example_inputs
        )

        shape_env = shape_env_from_inputs(example_inputs)

        fake_mode = detect_fake_mode(example_inputs)
        if not fake_mode:
            fake_mode = torch._subclasses.FakeTensorMode(allow_non_fake_inputs=True)
            FakeTensorProp(gm, mode=fake_mode).propagate(*example_inputs)
        else:
            FakeTensorProp(gm, mode=fake_mode).propagate_dont_convert_inputs(
                *example_inputs
            )
        with V.set_fake_mode(fake_mode):
            graph = GraphLowering(
                gm,
                shape_env=shape_env,
            )
            with V.set_graph_handler(graph), V.set_debug_handler(DebugContext()):
                graph.run(*example_inputs)
                graph.compile_to_module()
                scheduler_node = graph.scheduler.nodes[0]
                DataTypePropagation.propagate_scheduler_node(scheduler_node)
                root_graph = scheduler_node._body.root_block.graph
                for node in root_graph.nodes:
                    if node.op == "placeholder":
                        self.assertEqual(get_data_type(node), None)
                    elif node.target in boolean_ops():
                        self.assertEqual(get_data_type(node), torch.bool)
                    elif node.target in (
                        "constant",
                        "to_dtype",
                        "index_expr",
                    ):
                        self.assertEqual(get_data_type(node), node.args[-1])
                    elif node.target in (
                        "get_index",
                        "index_expr",
                    ):
                        self.assertEqual(get_data_type(node), torch.int64)
                    elif node.target in (
                        "load",
                        "store",
                    ):
                        self.assertEqual(
                            get_data_type(node), V.graph.get_dtype(node.args[1])
                        )
                    elif node.target == "reduction":
                        _, _, dtype, _, _, _, _ = node.args
                        self.assertEqual(get_data_type(node), dtype)
                    elif node.target.startswith("masked_subblock"):
                        """
                        masked_subblocks:
                        opcode       name       target     args                        kwargs
                        -----------  ---------  ---------  --------------------------  --------
                        placeholder  ops        ops        ()                          {}
                        call_module  get_index  get_index  ('index2',)                 {}
                        call_method  load       load       (ops, 'arg0_1', get_index)  {}
                        call_method  to_dtype   to_dtype   (ops, load, torch.float32)  {}
                        output       output     output     (to_dtype,)                 {}
                        """
                        self.assertEqual(get_data_type(node), torch.float)
                    elif node.target == "and_":
                        """
                        and_'s input is boolean_ops:
                        -----------  ---------  ---------  --------------------------  --------
                        call_method  and__22           and_              (ops, ge_15, lt_15)
                        -----------  ---------  ---------  --------------------------  --------
                        """
                        self.assertEqual(get_data_type(node), torch.bool)
                    elif node.target == "maximum":
                        """
                        maximum's input is maximum or masked_subblock:
                        -----------  ---------  ---------  --------------------------  --------
                        call_method  maximum_6         maximum           (ops, masked_subblock8, maximum_5)
                        -----------  ---------  ---------  --------------------------  --------
                        """
                        self.assertEqual(get_data_type(node), torch.float)
                    elif node.target == "output":
                        self.assertEqual(get_data_type(node), torch.bfloat16)