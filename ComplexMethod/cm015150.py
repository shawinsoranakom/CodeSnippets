def test_jit_alias_remapping(self, device, dtype, op):
        # NOTE: only tests on first sample
        samples = op.sample_inputs(device, dtype, requires_grad=True)
        sample = first_sample(self, samples)

        # [Scripting Data Preparation]
        # Prepare data for test scripting
        # Below we prepare strings of args/kwargs with and without type annotations.
        # These strings are inserted into function template strings which is then torch scripted.
        # - args string is ["t0"] corresponding to the "input" tensor required by the op
        # - args_kw is the value of args and strings of kwargs used to call the op (without type annotations), for example,
        # ["to", "1.0", "(1,)", "True", "tensor(1.0)"] -> def fn(t0): return variant(t0, 1.0, (1,), True, tensor(1.0))
        args = ["t0"]

        def quote_strs(v):
            if isinstance(v, str):
                return f"'{v}'"

            return str(v)

        args_kw = (
            args
            + [f"{v}" for v in sample.args]
            + [f"{k}={quote_strs(v)}" for k, v in sample.kwargs.items()]
        )

        # Prepare data for test tracing
        sample_args_kwargs = ()
        if len(sample.args) > 0:
            sample_args_kwargs += (sample.args,)
        if len(sample.kwargs) > 0:
            sample_args_kwargs += (sample.kwargs,)

        original_name = op.aten_name
        original_name_inplace = original_name + "_"
        expected_dtype = op(sample.input, *sample.args, **sample.kwargs).dtype

        for a_op in op.aliases:
            inplace = a_op.inplace_variant
            method_or_inplace = [a_op.inplace_variant, a_op.method_variant]
            variants = (
                v
                for v in (a_op.op, a_op.method_variant, a_op.inplace_variant)
                if v is not None
            )

            # Test scripting:
            for variant in variants:
                variant_name = variant.__name__
                op_name = original_name_inplace if variant is inplace else original_name

                if variant in method_or_inplace:
                    fn_template = """
                        def _fn(t0{c}):
                            return t0.{alias_name}({args_kw})
                    """
                    # remove the first input tensor
                    script = fn_template.format(
                        c=", " if len(args_kw[1:]) > 1 else "",
                        args_kw=", ".join(args_kw[1:]),
                        alias_name=variant_name,
                    )
                else:
                    fn_template = """
                        def _fn({args}):
                            return variant({args_kw})
                    """
                    script = fn_template.format(
                        args=", ".join(args),
                        args_kw=", ".join(args_kw),
                    )

                # Required to avoid undefined value: tensor error in JIT
                # compilation of the function template
                script = script.replace("tensor(", "torch.tensor(")

                scripted = torch.jit.CompilationUnit(script)._fn

                if variant is inplace and not torch.can_cast(expected_dtype, dtype):
                    try:
                        inp = clone_input_helper(sample.input)
                        scripted(inp)
                    except Exception:
                        continue
                    self.fail(
                        "Inplace operation on integer tensor that should be promoted to float didn't fail!"
                    )

                inp = clone_input_helper(sample.input)
                scripted(inp)
                inp = clone_input_helper(sample.input)
                graph = scripted.graph_for(inp)
                FileCheck().check(op.aten_name).check_not(variant_name).run(graph)

            # Test tracing:
            for variant in variants:
                variant_name = variant.__name__
                op_name = original_name_inplace if variant is inplace else original_name

                def _fn(*sample_args, **sample_kwargs):
                    return variant(*sample_args, **sample_kwargs)

                inp = (clone_input_helper(sample.input),) + sample_args_kwargs
                traced = torch.jit.trace(_fn, *inp)
                inp = (clone_input_helper(sample.input),) + sample_args_kwargs
                traced(*inp)
                inp = (clone_input_helper(sample.input),) + sample_args_kwargs
                graph = traced.graph_for(*inp)
                FileCheck().check(op_name).check_not(variant_name).run(graph)