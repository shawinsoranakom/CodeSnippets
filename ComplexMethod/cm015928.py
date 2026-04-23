def test_embedding(self):
        class BasicBlock(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.embedding = torch.nn.Embedding(256008, 1024, padding_idx=1)

            def forward(self, x: TensorType([2, 4])):
                return self.embedding(x)

        B = BasicBlock().forward(torch.ones([2, 4], dtype=torch.long)).size()
        ast_rewriter = RewritingTracer()
        graph = ast_rewriter.trace(BasicBlock())
        traced = GraphModule(ast_rewriter.root, graph, "gm")

        transformed = transform_all_constraints(traced, counter=0)
        s = z3.Solver()
        s.add(transformed)
        self.assertEqual(s.check(), z3.sat)
        embedding_result = z3.Const(2, tensor_type)

        if s.model()[embedding_result].arg(0).arg(1) != B[0]:
            raise AssertionError(
                f"Expected arg(0).arg(1) == {B[0]}, "
                f"got {s.model()[embedding_result].arg(0).arg(1)}"
            )
        if s.model()[embedding_result].arg(1).arg(1) != B[1]:
            raise AssertionError(
                f"Expected arg(1).arg(1) == {B[1]}, "
                f"got {s.model()[embedding_result].arg(1).arg(1)}"
            )
        if s.model()[embedding_result].arg(2).arg(1) != B[2]:
            raise AssertionError(
                f"Expected arg(2).arg(1) == {B[2]}, "
                f"got {s.model()[embedding_result].arg(2).arg(1)}"
            )

        # change the type. This should still be satisfiable
        for n in traced.graph.nodes:
            if n.op == "placeholder":
                n.type = TensorType([Dyn, Dyn])

        transformed = transform_all_constraints(traced, counter=0)
        s = z3.Solver()
        s.add(transformed)
        self.assertEqual(s.check(), z3.sat)
        if s.model()[embedding_result].arg(0).arg(0) != 0:
            raise AssertionError(
                f"Expected arg(0).arg(0) == 0, "
                f"got {s.model()[embedding_result].arg(0).arg(0)}"
            )
        if s.model()[embedding_result].arg(1).arg(0) != 0:
            raise AssertionError(
                f"Expected arg(1).arg(0) == 0, "
                f"got {s.model()[embedding_result].arg(1).arg(0)}"
            )
        if s.model()[embedding_result].arg(2).arg(1) != B[2]:
            raise AssertionError(
                f"Expected arg(2).arg(1) == {B[2]}, "
                f"got {s.model()[embedding_result].arg(2).arg(1)}"
            )

        # change the type to Dyn. Here, we will get an arbitrary migration
        for n in traced.graph.nodes:
            if n.op == "placeholder":
                n.type = Dyn

        transformed = transform_all_constraints(traced, counter=0)
        s = z3.Solver()
        s.add(transformed)

        self.assertEqual(s.check(), z3.sat)