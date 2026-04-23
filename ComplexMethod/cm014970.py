def test_normalize_operator_exhaustive(self, device, dtype, op):
        # These ops currently don't trace in FX for various reasons (i.e. they take a list of tensors)
        fx_fail = {"cat", "stack", "hstack", "vstack", "dstack", "linalg.multi_dot", "_upsample_bilinear2d_aa", "_chunk_cat"}
        sample_inputs_itr = op.sample_inputs(device, dtype, requires_grad=False)
        if isinstance(op.op, torch._ops.OpOverload):
            self.skipTest("normalize operator doesn't work on torch.ops")
        for sample_input in sample_inputs_itr:
            unsupported_arg_type = False
            arg_values = [sample_input.input] + list(sample_input.args)
            kwarg_values = sample_input.kwargs
            arg_types = []
            kwarg_types = {}

            def jit_infer_type(v):
                inferred_arg_type = torch._C._jit_try_infer_type(v)
                if not inferred_arg_type.success():
                    raise AssertionError("expected inferred_arg_type.success()")
                t = _torchscript_type_to_python_type(inferred_arg_type.type())
                return t

            for v in arg_values:
                if isinstance(v, torch.Tensor):
                    arg_types.append(type(v))
                else:
                    if isinstance(v, complex):
                        # Complex type not supported in FX
                        unsupported_arg_type = True
                    arg_types.append(jit_infer_type(v))

            for k, v in kwarg_values.items():
                if isinstance(v, torch.Tensor):
                    kwarg_types[k] = type(v)
                else:
                    if isinstance(v, complex):
                        # Complex type not supported in FX
                        unsupported_arg_type = True
                    kwarg_types[k] = jit_infer_type(v)

            if unsupported_arg_type:
                continue
            # Test normalize_function by itself
            ref_out = op.op(*arg_values, **kwarg_values)
            norm_args_and_kwargs = normalize_function(
                op.op, arg_values, kwarg_values, arg_types, kwarg_types
            )
            if norm_args_and_kwargs is None:
                raise RuntimeError(
                    """
                    FX failed to normalize op - add the op to the op_skip list.
                    A common reason is if your OpInfo was implemented with a lambda
                    - otherwise, file an issue
                    """
                )
            test_out = op.op(*norm_args_and_kwargs.args, **norm_args_and_kwargs.kwargs)
            self.assertEqual(test_out, ref_out)

            # Test normalized_arguments as part of FX
            if op.name in fx_fail:
                continue
            param_names = []
            param_values = []
            fx_args = []

            idx = 0

            def process_arg(arg, name):
                if isinstance(arg, torch.Tensor):
                    param_names.append(name)
                    param_values.append(arg)
                    return name
                else:
                    return f"{repr(arg)}"

            def process_arg_with_idx(arg):
                nonlocal idx
                res = process_arg(arg, f"arg_{idx}")
                idx = idx + 1
                return res

            def str_arg(arg):
                if isinstance(arg, tuple):
                    args = [f"{str_arg(v)}, " for v in arg]
                    return f"({' '.join(args)})"
                elif isinstance(arg, list):
                    args = [f"{str_arg(v)}" for v in arg]
                    return f"[{', '.join(args)}]"
                else:
                    return arg

            for v in arg_values:
                arg = pytree.tree_map(process_arg_with_idx, v)
                fx_args.append(str_arg(arg))

            for k, v in kwarg_values.items():
                arg = pytree.tree_map(functools.partial(process_arg, name=k), v)
                fx_args.append(f"{k} = {str_arg(arg)}")

            code = f"""
class TestModule(torch.nn.Module):
    def forward(self, {', '.join(param_names)}):
        return torch.{op.name}({', '.join(fx_args)})
            """

            g = {"torch": torch, "inf": math.inf}
            exec(code, g)
            TestModule = g["TestModule"]

            m = TestModule()
            traced = torch.fx.symbolic_trace(m)
            ref_out = traced(*param_values)

            for node in traced.graph.nodes:
                if node.op == "call_function":
                    normalized_args = node.normalized_arguments(
                        traced, arg_types, kwarg_types
                    )
                    if not normalized_args:
                        raise AssertionError("expected normalized_args to be truthy")
                    node.args = normalized_args.args
                    node.kwargs = normalized_args.kwargs
            traced.recompile()

            test_out = traced(*param_values)
            self.assertEqual(test_out, ref_out)