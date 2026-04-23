def _check_graph_nodes(self, gm1, gm2, _check_meta=True):
        # TODO: The _check_meta flag bypasses checking for
        # source_fn/nn_module_stack as there is an issue with
        # roundtripping the source_fn value on torch.ops.map nodes
        # original source_fn: <functorch.experimental._map.MapWrapper object at 0x7f80a0549930>
        # deserialized source_fn: 'functorch.experimental._map.map'

        self.assertEqual(len(gm1.graph.nodes), len(gm2.graph.nodes))

        for node1, node2 in zip(gm1.graph.nodes, gm2.graph.nodes):
            self.assertEqual(node1.op, node2.op)
            if node1.op == "call_function":
                # Check "val" metadata
                val1 = node1.meta.get("val", None)
                val2 = node2.meta.get("val", None)
                self.assertEqual(len(node1.args), len(node2.args))
                self.assertEqual(set(node1.kwargs.keys()), set(node2.kwargs.keys()))
                if val1 is None or val2 is None:
                    # Either both are None
                    self.assertEqual(val1, val2)
                elif isinstance(val1, FakeTensor) and isinstance(val2, FakeTensor):
                    # Or both are fake tensors with the same shape/dtype
                    self.assertEqual(len(val1.shape), len(val2.shape))
                    for s1, s2 in zip(val1.shape, val2.shape):
                        if is_concrete_int(s1) and is_concrete_int(s2):
                            self.assertEqual(s1, s2)
                        else:
                            self.assertEqual(str(s1), str(s2))
                    self.assertEqual(val1.dtype, val2.dtype)
                elif isinstance(val1, (list, tuple)) and isinstance(
                    val2, (list, tuple)
                ):
                    # Or both are fake tensors lists with one element and with the
                    # same shape/dtype
                    for v1, v2 in zip(
                        pytree.tree_leaves(val1), pytree.tree_leaves(val2)
                    ):
                        if isinstance(v1, FakeTensor):
                            self.assertEqual(v1.shape, v2.shape)
                            self.assertEqual(v1.dtype, v2.dtype)
                else:
                    # For expressions like 's0 < 10' can only compare through string
                    self.assertEqual(str(val1), str(val2))

                # Check "stack_trace" metadata
                self.assertEqual(
                    node1.meta.get("stack_trace", None),
                    node2.meta.get("stack_trace", None),
                )

                if node1.target == torch.ops.higher_order.cond:
                    true_graph1 = getattr(gm1, node1.args[1].target)
                    true_graph2 = getattr(gm2, node2.args[1].target)
                    self._check_graph_nodes(true_graph1, true_graph2)

                    false_graph1 = getattr(gm1, node1.args[2].target)
                    false_graph2 = getattr(gm2, node2.args[2].target)
                    self._check_graph_nodes(false_graph1, false_graph2)
                elif node1.target == torch.ops.higher_order.map_impl:
                    map_graph1 = getattr(gm1, node1.args[0].target)
                    map_graph2 = getattr(gm2, node2.args[0].target)
                    self._check_graph_nodes(map_graph1, map_graph2, False)

            if _check_meta and node1.op not in ("get_attr", "placeholder", "output"):
                # Check "nn_module_stack" metadata
                self.assertEqual(
                    node1.meta.get("nn_module_stack", None),
                    node2.meta.get("nn_module_stack", None),
                )
                # Check "source_fn_stack" metadata
                self.assertEqual(
                    node1.meta.get("source_fn_stack", None),
                    node2.meta.get("source_fn_stack", None),
                )