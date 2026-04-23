def backward(ctx: Any, *flat_args: Any) -> tuple[Any, ...]:
                # With boxed_grads_call, grads arrive as a single mutable
                # list (not *args) so backward can free them individually
                # to reduce peak memory.
                if CompiledFunction.boxed_grads_call:
                    if len(flat_args) != 1 or not isinstance(flat_args[0], list):
                        raise AssertionError(
                            "boxed_grads_call is set but backward received "
                            f"{len(flat_args)} args instead of a single mutable "
                            "list. When boxed_grads_call=True, grads must be "
                            "passed as a single list argument [grad0, grad1, ...] "
                            "to allow freeing individual grads mid-backward."
                        )
                    grad_args = flat_args[0]
                else:
                    # Non-boxed path: used by subclasses of CompiledFunction
                    # that override boxed_grads_call to False.
                    grad_args = list(flat_args)
                del flat_args
                all_args = _backward_prologue_functional(
                    saved_state.load_tensors(ctx),
                    ctx.symints,
                    ctx.opaque_objects,
                    CompiledFunction.metadata,
                    CompiledFunction.maybe_subclass_metadata,
                    grad_args,
                    codegen_unwrap_fn=CompiledFunction._bw_prologue_unwrap_fn,
                )
                rng_state.add_backward_args(ctx, all_args)

                def impl_fn(double_ctx: Any = None) -> Any:
                    out = CompiledFunction._backward_impl(ctx, all_args)
                    return _backward_epilogue_functional(
                        CompiledFunction.metadata,
                        CompiledFunction.maybe_subclass_metadata,
                        out,
                        codegen_wrap_fn=CompiledFunction._bw_epilogue_wrap_fn,
                    )

                if (
                    torch._C._is_key_in_tls("context")
                    and (config_ctx := torch._C._get_obj_in_tls("context")) is not None
                ):
                    impl_fn = functools.partial(config_ctx.run, impl_fn)

                needs_grad = torch.is_grad_enabled() and any(
                    t.requires_grad for t in all_args if isinstance(t, torch.Tensor)
                )
                if needs_grad:
                    # double backward
                    return CompiledFunction._double_backward(ctx, impl_fn, all_args)
                return impl_fn()