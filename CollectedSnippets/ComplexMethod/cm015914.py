def test_retain_node_meta(self):
        r"""
        Perform constant folding conversion, and validate that node meta is retained.
        """

        class ConstFoldTestModule(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.attr = torch.nn.Parameter(torch.randn(2, 3))

            def forward(self, x):
                a = self.attr + self.attr
                return x - a

        mod = ConstFoldTestModule()
        gm = torch.fx.symbolic_trace(mod)

        # Add a count for each node to check after we const fold.
        for idx, node in enumerate(gm.graph.nodes):
            if node.op != "output":
                node.meta["meta_idx"] = idx

        # Pre-folding:
        # idx 0: placeholder
        # idx 1: get_attr (will no longer be used, hence removed)
        # idx 2: add (will be folded into a get_attr)
        # idx 3: sub

        gm_folded: const_fold.FoldedGraphModule = const_fold.split_const_subgraphs(gm)
        self._verify_const_fold_mod(gm_folded)

        # Post-folding:
        # idx 0: placeholder
        # idx 2: get_attr (replaced original add; original get_attr was removed)
        # idx 3: sub

        # Check the expected indices are still here.
        for node in gm_folded.graph.nodes:
            if node.op == "placeholder":
                self.assertEqual(node.meta["meta_idx"], 0)
            elif node.op == "get_attr":
                self.assertEqual(node.meta["meta_idx"], 2)
            elif node.op == "call_function" and node.target == operator.sub:
                self.assertEqual(node.meta["meta_idx"], 3)
            else:
                self.assertEqual(node.op, "output")

        # Now run both folded and non-folded to check results equal.
        in_x = torch.randn(2, 3)
        fold_result = gm_folded(in_x)
        base_result = mod(in_x)
        self.assertTrue(torch.equal(fold_result, base_result))