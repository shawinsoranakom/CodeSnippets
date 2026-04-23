def _check_equal_ts_ep_converter(
        self,
        M,
        tracing_inputs,
        option: list[str] | None = None,
        check_persistent=False,
        lifted_tensor_constants=None,
        runtime_inputs: list[Any] | None = None,
    ) -> list[ExportedProgram]:
        # By default, it tests both jit.trace and jit.script.
        if option is None:
            option = ["trace", "script"]

        if check_persistent:
            num_iterations = 10
        else:
            num_iterations = 1

        ep_list = []
        for opt in option:
            if opt == "script":
                # Separate two models for testing non-functional effects
                if check_persistent:
                    original_ts_model = torch.jit.script(M())
                    ts_model = torch.jit.script(M())
                    eager_model = M()
                else:
                    original_ts_model = torch.jit.script(M)
                    ts_model = torch.jit.script(M)
                    eager_model = M
            elif opt == "trace":
                if check_persistent:
                    original_ts_model = torch.jit.trace(M(), tracing_inputs)
                    ts_model = torch.jit.trace(M(), tracing_inputs)
                    eager_model = M()
                else:
                    original_ts_model = torch.jit.trace(M, tracing_inputs)
                    ts_model = torch.jit.trace(M, tracing_inputs)
                    eager_model = M
            else:
                raise RuntimeError(f"Unrecognized mode for torch.jit: {opt}")

            converter = TS2EPConverter(ts_model, tracing_inputs)
            ep = converter.convert()
            ep_list.append(ep)

            if runtime_inputs is None:
                runtime_inputs = []

            for inp in [tracing_inputs] + runtime_inputs:
                for _ in range(num_iterations):
                    orig_out, _ = pytree.tree_flatten(original_ts_model(*inp))
                    ep_out, _ = pytree.tree_flatten(ep.module()(*inp))

                    # Check module.
                    if isinstance(eager_model, torch.nn.Module):
                        expected_state_dict = OrderedDict()
                        expected_state_dict.update(ts_model.state_dict())
                        if lifted_tensor_constants:
                            expected_state_dict.update(lifted_tensor_constants)
                        self.assertEqual(
                            ep.state_dict.keys(),
                            expected_state_dict.keys(),
                        )

                    # Check results
                    self._check_tensor_list_equal(ep_out, orig_out)
        return ep_list