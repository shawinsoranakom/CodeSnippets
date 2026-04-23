def propagate_mutation(
        self,
        fx_node: torch.fx.Node,
        old_args: tuple[Any],
        old_kwargs: dict[str, Any],
        new_args: tuple[Any],
        new_kwargs: dict[str, Any],
    ) -> None:
        """Propagate mutations on new_args/new_kwargs back to old_args/old_kwargs.

        Assumes we may have cloned old_args/old_kwargs into new_args/new_kwargs
        and then called fx_node(*new_args, **new_kwargs).

        If fx_node mutates any of new_args/new_kwargs, and they are different from
        old_args/old_kwargs, then we need to update the original tensor.
        """
        assert len(old_args) == len(new_args)
        assert len(old_kwargs) == len(new_kwargs)

        if fx_node.target is torch.ops.higher_order.triton_kernel_wrapper_mutation:
            kwargs = fx_node.kwargs["kwargs"]
            assert isinstance(kwargs, dict)
            mutated = torch._higher_order_ops.triton_kernel_wrap.get_mutated_tensors(
                old_kwargs["kernel_idx"],
                old_kwargs["constant_args_idx"],
                {
                    k: v.meta["val"] if isinstance(v, torch.fx.Node) else v
                    for k, v in kwargs.items()
                },
                old_kwargs["tma_descriptor_metadata"],
            )
            for name in mutated:
                old_arg = old_kwargs["kwargs"][name]
                new_arg = new_kwargs["kwargs"][name]
                if old_arg is new_arg:
                    continue

                self.call_function(torch.ops.aten.copy_.default, (old_arg, new_arg), {})
            return

        assert isinstance(fx_node.target, torch._ops.OpOverload)

        def maybe_propagate(
            schema_arg: torch._C.Argument, old_arg: ir.IRNode, new_arg: ir.IRNode
        ) -> None:
            if old_arg is new_arg:
                return
            if schema_arg.alias_info is not None and schema_arg.alias_info.is_write:
                # The lowering for copy_ is smart enough to "replace" old_arg with
                # new_arg in all future uses so a copy_ kernel never gets emitted.
                # old_arg, new_arg may be immutable_list
                if isinstance(old_arg, ir.IRNode):
                    old_arg = (old_arg,)  # type: ignore[assignment]
                    new_arg = (new_arg,)  # type: ignore[assignment]

                for old_arg_item, new_arg_item in zip(old_arg, new_arg):  # type: ignore[call-overload]
                    if old_arg_item is new_arg_item:
                        continue
                    self.call_function(
                        torch.ops.aten.copy_.default, (old_arg_item, new_arg_item), {}
                    )

        schema = fx_node.target._schema
        for idx, (old_arg, new_arg) in enumerate(zip(old_args, new_args)):
            schema_arg = schema.arguments[idx]
            maybe_propagate(schema_arg, old_arg, new_arg)

        schema_kwargs = {arg.name: arg for arg in schema.arguments}

        for key in old_kwargs:
            old_arg = old_kwargs[key]
            new_arg = new_kwargs[key]
            schema_arg = schema_kwargs[key]
            maybe_propagate(schema_arg, old_arg, new_arg)