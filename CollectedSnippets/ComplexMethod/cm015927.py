def test_getitem_tensor(self):
        class BasicBlock(torch.nn.Module):
            def forward(self, x: TensorType([4, 4])):
                getitem = x[
                    (None, None, slice(None, None, None), slice(None, None, None))
                ]
                return getitem

        B = BasicBlock()
        b = B.forward(torch.rand(4, 4))

        symbolic_traced: torch.fx.GraphModule = symbolic_trace(B)
        transformed = transform_all_constraints(symbolic_traced, counter=0)

        s = z3.Solver()
        s.add(transformed)
        self.assertEqual(s.check(), z3.sat)
        get_item_res = z3.Const(2, tensor_type)
        if s.model()[get_item_res].arg(0).arg(1) != b.shape[0]:
            raise AssertionError(
                f"Expected arg(0).arg(1) == {b.shape[0]}, "
                f"got {s.model()[get_item_res].arg(0).arg(1)}"
            )
        if s.model()[get_item_res].arg(1).arg(1) != b.shape[1]:
            raise AssertionError(
                f"Expected arg(1).arg(1) == {b.shape[1]}, "
                f"got {s.model()[get_item_res].arg(1).arg(1)}"
            )
        if s.model()[get_item_res].arg(2).arg(1) != b.shape[2]:
            raise AssertionError(
                f"Expected arg(2).arg(1) == {b.shape[2]}, "
                f"got {s.model()[get_item_res].arg(2).arg(1)}"
            )
        if s.model()[get_item_res].arg(3).arg(1) != b.shape[3]:
            raise AssertionError(
                f"Expected arg(3).arg(1) == {b.shape[3]}, "
                f"got {s.model()[get_item_res].arg(3).arg(1)}"
            )

        # change the annotation on the input to make sure it propagates
        # to the output
        for n in symbolic_traced.graph.nodes:
            if n.op == "placeholder":
                n.type = TensorType([Dyn, 4])

        transformed = transform_all_constraints(symbolic_traced, counter=0)
        s = z3.Solver()
        s.add(transformed)
        self.assertEqual(s.check(), z3.sat)
        # dyn check
        if s.model()[get_item_res].arg(2).arg(0) != 0:
            raise AssertionError(
                f"Expected arg(2).arg(0) == 0, "
                f"got {s.model()[get_item_res].arg(2).arg(0)}"
            )