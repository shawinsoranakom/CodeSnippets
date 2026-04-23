def test_backward_nodes_have_seq_nr_under_non_strict(self):
        class Model(nn.Module):
            def __init__(self):
                super().__init__()
                self.w = nn.Parameter(torch.randn(4, 4))

            def forward(self, x):
                return checkpoint(
                    lambda x: torch.sin(x @ self.w), x, use_reentrant=False
                )

        gm = self._trace_train_step(Model(), torch.randn(2, 4))
        forward_seq_nrs = {
            node.meta["seq_nr"]
            for node in gm.graph.nodes
            if node.op == "call_function"
            and not node.meta.get("autograd_backward", False)
            and "seq_nr" in node.meta
        }
        backward_seq_nrs = {
            node.meta["seq_nr"]
            for node in gm.graph.nodes
            if node.op == "call_function"
            and node.meta.get("autograd_backward", False)
            and "seq_nr" in node.meta
        }

        self.assertTrue(forward_seq_nrs)
        self.assertTrue(backward_seq_nrs)
        self.assertSetEqual(backward_seq_nrs, forward_seq_nrs)