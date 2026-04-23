def __torch_dispatch__(
        self,
        func: OpOverload,
        types: Sequence[type],
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
    ) -> Any:
        if kwargs is None:
            kwargs = {}

        if _has_unrecognized_tensor_types(types):
            return NotImplemented

        if (
            func not in FunctionalTensor.metadata_fns
            and self._can_decompose(func, args, kwargs)
            # Not all funcs from __torch_dispatch__ are actual dispatcher ops,
            # e.g. prim.device
            and torch._C._dispatch_has_kernel(func.name())
        ):
            with self:
                r = func.decompose(*args, **kwargs)
                if r is not NotImplemented:
                    return r

        def wrap(x: object) -> object:
            # Only wrap our outputs in subclasses if the inner functionalization call
            # also wrapped outputs into FunctionalTensorWrappers.
            # When can this happen? e.g. `torch.div(2, 2)`
            if isinstance(x, FunctionalTensor):
                raise AssertionError("x must not be a FunctionalTensor in wrap()")
            if isinstance(x, torch.Tensor) and torch._is_functional_tensor(x):
                return FunctionalTensor(x, self)
            return x

        def unwrap(x: FunctionalTensor) -> torch.Tensor:
            return x.elem

        from torch._higher_order_ops.auto_functionalize import (
            can_auto_functionalize,
            do_auto_functionalize,
            do_auto_functionalize_v2,
        )

        if can_auto_functionalize(
            func
        ) and not torch._C._dispatch_has_kernel_for_dispatch_key(
            func.name(), torch._C.DispatchKey.Functionalize
        ):
            import torch._export.config as export_config
            import torch._inductor.config as inductor_config

            if torch.compiler.is_exporting():
                # NB: out= ops are not yet handled here; they only go through v2 below.
                if export_config.enable_auto_functionalized_v2_for_export:
                    return do_auto_functionalize_v2(self, func, args, kwargs)

                return do_auto_functionalize(self, func, args, kwargs)

            if inductor_config.enable_auto_functionalized_v2 or (
                isinstance(func, torch._ops.OpOverload)
                and torch._library.utils.is_out(func)
            ):
                return do_auto_functionalize_v2(self, func, args, kwargs)
            return do_auto_functionalize(self, func, args, kwargs)

        from torch._higher_order_ops.effects import handle_effects, has_effects

        if has_effects(func):
            if torch._C._dispatch_has_kernel_for_dispatch_key(
                func.name(), torch._C.DispatchKey.Functionalize
            ):
                raise AssertionError(
                    f"func {func.name()} with effects should not have a kernel for Functionalize dispatch key"
                )
            return handle_effects(
                self._allow_token_discovery, self._tokens, func, args, kwargs
            )

        args_unwrapped, kwargs_unwrapped = pytree.tree_map_only(
            FunctionalTensor, unwrap, (args, kwargs)
        )

        # Expectation: functionalization should not **already** be enabled above our mode.
        # Why would that be bad? when we return a FunctionalTensor here, we don't want functionalization
        # to run above this mode and further wrap that output in **another** C++ FunctionalTensorWrapper.
        _assert_functionalize_not_active(
            "Functionalization should not already be enabled above this mode"
        )
        include_to_set = (
            torch._C._dispatch_tls_local_include_set()
            | torch._C.DispatchKeySet(torch._C.DispatchKey.Functionalize)
        )
        exclude_to_set = (
            torch._C._dispatch_tls_local_exclude_set().remove(
                torch._C.DispatchKey.Functionalize
            )
            - FunctionalTensor._extra_dispatch_keys
        )

        if isinstance(func, TorchBindOpOverload):
            # When the function is a TorchBindOpOverload, meaning some of the
            # inputs are FakeScriptObjects, we need to skip c++ dispatcher and
            # dispatch in python because C++ dispatcher will check the schema
            # and cannot recognize FakeScriptObject.
            ctx = PythonFunctionalizeAPI()
            fully_unwrapped_args = ctx.unwrap_tensors(args)
            fully_unwrapped_kwargs = ctx.unwrap_tensors(
                kwargs  # pyrefly: ignore[bad-argument-type]
            )
            outs_unwrapped = func(
                *fully_unwrapped_args,
                **fully_unwrapped_kwargs,
            )
            outs_wrapped = ctx.wrap_tensors(outs_unwrapped)
        else:
            # All we want to do here is reuse the existing C++ functionalization logic.
            # This requires swizzling our TLS dispatch keys so that the Functionalize key is active.
            with torch._C._ForceDispatchKeyGuard(include_to_set, exclude_to_set):
                try:
                    # By default for python functionalization (for AOTAutograd), we reapply views.
                    old_apply_views = torch._functionalize_enable_reapply_views(True)  # type: ignore[attr-defined]

                    # Sometimes these functions cannot be directly dispatched to functionalize key
                    # because args are sometimes not functional tensors for some reason?
                    if func in FunctionalTensor.metadata_fns:
                        outs_unwrapped = func(*args_unwrapped, **kwargs_unwrapped)
                        outs_wrapped = pytree.tree_map_only(
                            torch.Tensor, wrap, outs_unwrapped
                        )
                    else:
                        self._sync_view_replay_annotations(args, kwargs)

                        # When we dispatch to the C++ functionalization kernel, we might need to jump back to the
                        # PreDispatch mode stack afterwards, to handle any other PreDispatch modes underneath
                        # FunctionalTensorMode. If we call func() directly, we would need to exclude PreDispatch
                        # from the TLS in order to avoid infinite looping, but this would prevent us from coming
                        # back to PreDispatch later
                        outs_unwrapped = func._op_dk(
                            torch._C.DispatchKey.Functionalize,
                            *args_unwrapped,
                            **kwargs_unwrapped,
                        )

                        if self.export:
                            if func is torch.ops.aten.dropout.default:
                                torch._freeze_functional_tensor(outs_unwrapped)  # type: ignore[attr-defined]
                        outs_wrapped = pytree.tree_map_only(
                            torch.Tensor, wrap, outs_unwrapped
                        )
                finally:
                    torch._disable_functionalization()
                    torch._functionalize_enable_reapply_views(old_apply_views)  # type: ignore[attr-defined]

        _assert_functionalize_not_active(
            "Functionalization should not already be enabled above this mode after dispatch"
        )

        if (
            # If no outputs are our functional subclass, then don't try to fix up aliasing
            not any(
                isinstance(x, FunctionalTensor)
                for x in pytree.tree_leaves(outs_wrapped)
            )
            # Since lift_fresh lifts its argument into a functional tensor, we can skip the
            # aliasing correction step. Otherwise, we would be setting the storage of a
            # lifted tensor to that of an unlifted tensor.
            # Ref: https://github.com/pytorch/pytorch/issues/111506
            or func is torch.ops.aten.lift_fresh.default
        ):
            return outs_wrapped
        # for metadata mutations, need to manually mutate the metadata of the FunctionalTensor wrapper
        if (
            torch.Tag.inplace_view in func.tags
            and func is not torch.ops.aten.set_.source_Tensor
        ):
            with torch.utils._mode_utils.no_dispatch():
                func(*args, **kwargs)
        # Wrapper tensor subclasses do not have correct aliasing info! Use this util to manually correct the output aliasing.
        # inplace ops like `aten.add_()` are expected to return inputs **directly**, instead of creating fresh tensor objects.
        # Use this util to figure out the right thing to return.
        # If none of our inputs were wrapped, then we have no FunctionalTensor outputs that we need to fix up storages for.
        return return_and_correct_aliasing(func, args, kwargs, outs_wrapped)