def test_subgraph_creation(self, use_lazy):
        class MyModule(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.param = torch.nn.Parameter(torch.rand(3, 4))
                self.linear = torch.nn.Linear(4, 5)

            def forward(self, x, y):
                z = self.linear(x + self.param).clamp(min=0.0, max=1.0)
                w = self.linear(y).clamp(min=0.0, max=1.0)
                return z + w

        # symbolically trace model
        my_module = MyModule()
        my_module_traced = symbolic_trace(my_module)

        # random mod partitioning
        partition_counter = 0
        NPARTITIONS = 3

        # Add some random meta info to make sure it is kept around.
        for node in my_module_traced.graph.nodes:
            if node.op != "output":
                node.meta["test_meta_info"] = True

        def mod_partition(node: Node):
            nonlocal partition_counter
            partition = partition_counter % NPARTITIONS
            partition_counter = (partition_counter + 1) % NPARTITIONS
            return partition

        # split module in module with submodules
        with _use_lazy_graph_module(use_lazy):
            module_with_submodules = split_module(
                my_module_traced, my_module, mod_partition
            )

        # Check that test_meta_info was still on all nodes.
        submodules = dict(module_with_submodules.named_modules())
        for node in module_with_submodules.graph.nodes:
            if node.op == "call_module":
                submod = submodules[node.target]
                self.assertTrue(isinstance(submod, torch.fx.GraphModule))
                for submod_node in submod.graph.nodes:
                    if submod_node.op != "output":
                        stored_op = submod_node.meta.get("test_meta_info")
                        self.assertTrue(stored_op is not None and stored_op)

        x = torch.rand(3, 4)
        y = torch.rand(3, 4)

        orig_out = my_module_traced(x, y)
        submodules_out = module_with_submodules(x, y)

        self.assertEqual(orig_out, submodules_out)