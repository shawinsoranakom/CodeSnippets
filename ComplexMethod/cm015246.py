def test_stack_trace_make_fx(self):
        class Foo(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.linear = torch.nn.Linear(4, 4)

            def forward(self, x):
                x = self.linear(x)
                x *= 2.0
                return x

        inp = torch.randn(4, 4)
        gm = torch.fx.experimental.proxy_tensor.make_fx(
            Foo(), record_stack_traces=True
        )(
            inp,
        )

        # check correct lines are in stack trace
        trace_mul = [node for node in gm.graph.nodes if node.name == "mul_"][
            0
        ].meta.get("stack_trace", "")
        self.assertTrue(
            re.search(r"test_export.py.*in forward\n.*x \*= 2.0", trace_mul)
        )
        trace_addmm = [node for node in gm.graph.nodes if node.name in ["addmm", "t"]][
            0
        ].meta.get("stack_trace", "")
        self.assertTrue(
            re.search(
                r"test_export.py.*in forward\n.*x = self.linear\(x\)", trace_addmm
            )
        )

        # check correct lines are still in stack trace after export
        ep = export(
            gm,
            (torch.randn(4, 4),),
        ).run_decompositions({})
        # check correct lines are in stack trace
        trace_mul = [node for node in ep.graph.nodes if node.name == "mul"][0].meta.get(
            "stack_trace", ""
        )
        self.assertTrue(
            re.search(r"test_export.py.*in forward\n.*x \*= 2.0", trace_mul)
        )
        trace_addmm = [
            node for node in ep.graph.nodes if node.name in ["addmm", "linear"]
        ][0].meta.get("stack_trace", "")
        self.assertTrue(
            re.search(
                r"test_export.py.*in forward\n.*x = self.linear\(x\)", trace_addmm
            )
        )