def test_predispatch_grad_wrappers(self):
        class Model(torch.nn.Module):
            def forward(self, x, y):
                with torch.enable_grad():
                    x = x - y
                with torch.no_grad():
                    x = x + y
                return x

        # no grad
        model = Model()
        with torch.no_grad():
            ep_nograd = torch.export.export(
                model,
                (torch.tensor(10), torch.tensor(12)),
                {},
                dynamic_shapes=None,
                strict=False,
            )
        # check that only sub op is wrapped with grad_enabled
        getattr_nodes = [
            node for node in ep_nograd.graph.nodes if node.op == "get_attr"
        ]
        self.assertEqual(len(getattr_nodes), 1)
        grad_subgraph = getattr(ep_nograd.graph_module, getattr_nodes[0].target)
        op_node = [
            node for node in grad_subgraph.graph.nodes if node.op == "call_function"
        ][0]
        self.assertEqual(op_node.target._name, "aten::sub.Tensor")

        # enable grad
        model = Model()
        ep_grad = torch.export.export(
            model,
            (torch.tensor(10), torch.tensor(12)),
            {},
            dynamic_shapes=None,
            strict=False,
        )
        # check that only add op is wrapped with grad_enabled
        getattr_nodes = [node for node in ep_grad.graph.nodes if node.op == "get_attr"]
        self.assertEqual(len(getattr_nodes), 1)
        grad_subgraph = getattr(ep_grad.graph_module, getattr_nodes[0].target)
        op_node = [
            node for node in grad_subgraph.graph.nodes if node.op == "call_function"
        ][0]
        self.assertEqual(op_node.target._name, "aten::add.Tensor")