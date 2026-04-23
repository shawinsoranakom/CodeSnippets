def _run_test(
        self,
        model,
        inputs,
        device,
        dynamic=False,
        num_predicates=1,
    ):
        cnt = torch._dynamo.testing.CompileCounterWithBackend("inductor")
        compiled_model = torch.compile(backend=cnt, fullgraph=True)(model)

        inputs = [inp.to(device=device) for inp in inputs]
        input_sets = [inputs]
        if dynamic:
            larger_inputs = []
            for inp in inputs:
                # only tile non-scalar tensor inputs
                if inp.ndim > 0:
                    # tile every first dim 5x
                    tiling = [5] + [1] * (inp.ndim - 1)
                    larger_inputs.append(torch.tile(inp, tiling))
                else:
                    larger_inputs.append(inp)
            input_sets.append(larger_inputs)
            for inputs in input_sets:
                for inp in inputs:
                    # mark every first dim as dynamic
                    torch._dynamo.mark_dynamic(inp, 0)

        for inputs in input_sets:
            for inputs_with_predicates in prepend_predicates(
                inputs, num_predicates, device=device
            ):
                cloned_inputs = [inp.clone() for inp in inputs_with_predicates]
                result = model(*inputs_with_predicates)
                result_compiled = compiled_model(*inputs_with_predicates)
                # inputs must not be mutated
                torch.testing.assert_close(cloned_inputs, inputs_with_predicates)
                torch.testing.assert_close(result, result_compiled)

        self.assertEqual(cnt.frame_count, 1, "only one compilation expected")