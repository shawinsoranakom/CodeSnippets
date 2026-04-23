def test_stack_trace_preserved_linear(self):
        class M(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.linear = nn.Linear(1, 1)

            def forward(self, x):
                x = self.linear(x)
                return x

        m = M().eval()
        mp = prepare_fx(m, get_default_qconfig_mapping(), example_inputs=(torch.randn(1, 1),))

        found_stack_trace = False
        for n in mp.graph.nodes:
            if n.op == 'call_module' and n.target == 'linear':
                found_stack_trace = n.stack_trace is not None
                break
        self.assertTrue(found_stack_trace)

        # test reference model
        mq = convert_to_reference_fx(copy.deepcopy(mp))
        found_stack_trace = False
        for n in mq.graph.nodes:
            if n.op == 'call_module' and n.target == 'linear':
                found_stack_trace = n.stack_trace is not None
                break
        self.assertTrue(found_stack_trace, f"stack trace not found, node: {n.format_node()}, is_reference: True")

        # test quantized model
        mq = convert_fx(mp)
        found_stack_trace = False
        for n in mq.graph.nodes:
            if n.op == 'call_module' and n.target == 'linear':
                found_stack_trace = n.stack_trace is not None
                break
        self.assertTrue(found_stack_trace, f"stack trace not found, node: {n.format_node()}, is_reference: False")