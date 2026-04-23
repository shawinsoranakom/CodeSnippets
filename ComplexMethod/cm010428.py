def gen_schema(
        self,
        real_fn_callable,
        fake_fn_callable,
        input_spec,
        mutated_arg_indices,
        *flat_args,
        requires_grad_indices="",
    ):
        from torch._higher_order_ops.schema import HopSchemaGenerator
        from torch._higher_order_ops.utils import _maybe_fake_prop_ignore_unbacked
        from torch.fx.experimental.proxy_tensor import disable_proxy_modes_tracing

        mutated_set = _parse_mutated_arg_indices(mutated_arg_indices)

        with disable_proxy_modes_tracing():
            if mutated_set:
                schema_flat_args = tuple(
                    arg.detach().clone()
                    if isinstance(arg, torch.Tensor) and i in mutated_set
                    else arg
                    for i, arg in enumerate(flat_args)
                )
            else:
                schema_flat_args = flat_args

            def run_fake(*unfunc_flat_args):
                with unflatten_args_with_modules(unfunc_flat_args, input_spec) as (
                    args,
                    kwargs,
                ):
                    return fake_fn_callable(*args, **kwargs)

            fake_outputs = _maybe_fake_prop_ignore_unbacked(run_fake, schema_flat_args)

        gen = HopSchemaGenerator(self)
        gen.add_arg("real_fn_callable", real_fn_callable)
        gen.add_arg("fake_fn_callable", fake_fn_callable)
        gen.add_arg("input_spec", input_spec)
        gen.add_arg("mutated_arg_indices", mutated_arg_indices)
        for i, arg in enumerate(flat_args):
            gen.add_arg(f"arg{i}", arg, is_mutated=i in mutated_set)
        gen.add_arg(
            "requires_grad_indices",
            requires_grad_indices,
            default_value="",
            kw_only=True,
        )

        if isinstance(fake_outputs, tuple):
            for out in fake_outputs:
                gen.add_output(out)
        else:
            if fake_outputs is not None:
                raise AssertionError(
                    f"Expected fake_outputs to be a tuple or None, got {type(fake_outputs)}"
                )
            gen.add_output(fake_outputs)

        return gen.gen_schema()