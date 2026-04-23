def build(self) -> type[torch.autograd.Function]:
        compile_id = CompileContext.current_compile_id()
        compile_id_str = str(compile_id) if compile_id is not None else None
        self.spec.fw_metadata.compile_id_str = compile_id_str

        saved_state = _AutogradSavedState(self.spec.fw_metadata)
        forward_epilogue = _AutogradForwardEpilogue(self.spec.fw_metadata)
        rng_state = _AutogradRngStateTracker(
            num_rng=self.spec.fw_metadata.num_graphsafe_rng_states,
            graphsafe_idx=self.spec.fw_metadata.graphsafe_rng_state_index,
        )
        backward_compiler = _AutogradBackwardCompiler(
            compiled_bw=self.spec.compiled_bw_func,
            lazy_backward_info=self.spec.lazy_backward_info,
            disable_amp=self.spec.disable_amp,
            aot_config=self.spec.aot_config,
            fw_metadata=self.spec.fw_metadata,
            try_save_cache_entry=self.spec.try_save_cache_entry,
        )

        compiled_fw_func = self.spec.compiled_fw_func
        compiled_bw_func = self.spec.compiled_bw_func
        maybe_subclass_meta = self.spec.maybe_subclass_meta
        num_symints_saved_for_bw_ = self.spec.num_symints_saved_for_bw
        backward_state_indices = self.spec.backward_state_indices
        disable_amp = self.spec.disable_amp
        lazy_backward_info = self.spec.lazy_backward_info
        aot_config = self.spec.aot_config
        fw_metadata = self.spec.fw_metadata

        _codegen_bw_unwrap_fn = None
        _codegen_bw_wrap_fn = None
        if maybe_subclass_meta is not None:
            from .subclass_codegen import codegen_backward_subclass_fns

            _codegen_bw_unwrap_fn, _codegen_bw_wrap_fn = codegen_backward_subclass_fns(
                grad_input_metas=maybe_subclass_meta.grad_input_metas,
            )

        # Codegen for CompiledFunction.forward: emit straight-line TensorAlias
        # wrapping, _unsafe_view, and non-differentiable output collection with
        # all indices resolved at compile time.
        num_mutated_runtime_inps = fw_metadata.num_mutated_inp_runtime_indices
        num_outputs = fw_metadata.num_outputs
        num_outputs_aliased = fw_metadata.num_outputs_aliased

        _xform_lines = ["def _transform_raw_returns(raw_returns):"]
        _xform_globals: dict[str, object] = {
            "TensorAlias": TensorAlias,
            "torch": torch,
            "Tensor": Tensor,
        }

        for i, idx in enumerate(fw_metadata.mutated_inp_runtime_indices):
            info = fw_metadata.input_info[idx]
            if info.mutates_metadata and not info.mutates_data:
                _xform_lines.append(
                    f"    raw_returns[{i}] = TensorAlias(raw_returns[{i}])"
                )

        if fw_metadata.num_unsafe_view_outputs > 0:
            for idx in fw_metadata.unsafe_view_out_indices:
                ri = num_mutated_runtime_inps + idx
                _xform_lines.append(f"    _o = raw_returns[{ri}]")
                _xform_lines.append(
                    f"    raw_returns[{ri}] = torch.ops.aten._unsafe_view(_o, _o.shape)"
                )

        if num_outputs_aliased > 0:
            for idx in fw_metadata.aliased_out_indices:
                ri = num_mutated_runtime_inps + idx
                _xform_lines.append(
                    f"    raw_returns[{ri}] = TensorAlias(raw_returns[{ri}])"
                )

        # Non-differentiable output collection: build a list of specific indices
        # at compile time rather than iterating at runtime.
        _non_diff_indices: list[int] = []
        _returns_meta = [
            x
            for x in fw_metadata.input_info
            if x.mutation_type == MutationType.MUTATED_OUT_GRAPH
        ] + list(fw_metadata.output_info)
        for i, meta in enumerate(_returns_meta):
            if i < num_mutated_runtime_inps + num_outputs and not meta.requires_grad:
                _non_diff_indices.append(i)
        if _non_diff_indices:
            checks = " + ".join(
                f"([raw_returns[{i}]] if isinstance(raw_returns[{i}], Tensor) else [])"
                for i in _non_diff_indices
            )
            _xform_lines.append(f"    non_diff = {checks}")
        else:
            _xform_lines.append("    non_diff = []")
        _xform_lines.append("    return non_diff")

        _xform_source = "\n".join(_xform_lines)

        from .subclass_codegen import _compile_and_exec_source

        _codegen_transform_raw_returns: Callable[..., list[Any]] = (
            _compile_and_exec_source(  # type: ignore[assignment]
                _xform_source,
                _xform_globals,
                "_transform_raw_returns",
                "compiled_fn_wrapper",
            )
        )

        # Monkey-patch forward_epilogue.finalize to use codegen'd transform
        def _codegen_finalize(ctx: Any, fw_outs: Any) -> tuple[Any, ...]:
            num_forward_returns = fw_metadata.num_forward_returns
            raw_returns = list(fw_outs[:num_forward_returns])
            fw_outs_not_requiring_grad = _codegen_transform_raw_returns(raw_returns)
            if config.debug_assert:
                if num_mutated_runtime_inps > 0:
                    user_mutated_inputs_raw = raw_returns[0:num_mutated_runtime_inps]
                    mut_inp_infos = [
                        x
                        for x in fw_metadata.input_info
                        if x.mutates_data or x.mutates_metadata
                    ]
                    if len(user_mutated_inputs_raw) != len(mut_inp_infos):
                        raise AssertionError(
                            f"expected len(user_mutated_inputs_raw) == len(mut_inp_infos), "
                            f"got {len(user_mutated_inputs_raw)} != {len(mut_inp_infos)}"
                        )
                if num_outputs_aliased > 0:
                    intermediates_raw = raw_returns[
                        num_mutated_runtime_inps + num_outputs :
                    ]
                    if any(isinstance(x, TensorAlias) for x in intermediates_raw):
                        raise AssertionError(
                            "expected no TensorAlias in intermediates_raw"
                        )
            ctx.mark_non_differentiable(*fw_outs_not_requiring_grad)
            ctx._materialize_non_diff_grads = False
            return tuple(raw_returns)

        forward_epilogue.finalize = _codegen_finalize  # type: ignore[method-assign]

        class CompiledFunction(torch.autograd.Function):
            compiled_fw = compiled_fw_func
            compiled_bw = compiled_bw_func
            metadata: ViewAndMutationMeta = fw_metadata  # type: ignore[assignment]
            maybe_subclass_metadata: SubclassMeta | None = maybe_subclass_meta
            num_symints_saved_for_bw = num_symints_saved_for_bw_
            _aot_id = aot_config.aot_id
            _lazy_backward_info = lazy_backward_info
            _bw_epilogue_wrap_fn = _codegen_bw_wrap_fn
            _bw_prologue_unwrap_fn = _codegen_bw_unwrap_fn
            boxed_grads_call = True

            @staticmethod
            def _compiled_autograd_key(ctx: Any) -> tuple[Any, ...]:
                return (ctx._autograd_function_id, *ctx.symints)

            @staticmethod
            # pyrefly: ignore [bad-override]
            def forward(ctx: Any, *deduped_flat_tensor_args: Any) -> Any:
                args = deduped_flat_tensor_args
                if backward_state_indices:
                    bw_state = args[backward_state_indices[0]]
                    if not isinstance(bw_state, BackwardState):
                        raise AssertionError(
                            f"expected BackwardState, got {type(bw_state)}"
                        )
                    ctx._compiled_autograd_backward_state = bw_state

                args = rng_state.add_forward_args(ctx, args)

                # There is a pretty complicated calling convention around what the compiled fw returns.
                # The full list of outputs and their relative order is:
                # (*tokens, *mutated_inputs, *fw_outs, *fw_intermediate_bases, *saved_tensors, *saved_symints)
                # - Note that in the synthetic bases case, mutated_inputs will correspond to an updated version
                #   of the original view, and not the synthetic base
                # - Note that donated buffer logic requires (*saved_tensors, *saved_symints) showing up last
                #   in the fw output order.
                fw_outs = call_func_at_runtime_with_args(
                    CompiledFunction.compiled_fw,
                    # pyrefly: ignore [bad-argument-type]
                    args,
                    disable_amp=disable_amp,
                )

                saved_state.save_from_forward(ctx, fw_outs)
                return forward_epilogue.finalize(ctx, fw_outs)

            @staticmethod
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

            @staticmethod
            def _double_backward(
                ctx: Any, impl_fn: Callable[..., Any], all_args: list[Any]
            ) -> Any:
                # Ensure that the graph is connected, and error if double backward is performed.
                # See comment for why once_differentiable is not sufficient:
                # https://github.com/pytorch/pytorch/pull/92348/files#r1072962107
                class CompiledFunctionBackward(torch.autograd.Function):
                    # CompiledFunctionBackward is not yet supported in dynamo skipfiles
                    _aot_id = aot_config.aot_id

                    @staticmethod
                    # pyrefly: ignore [bad-override]
                    def forward(double_ctx: Any, *unused_args: Any) -> Any:
                        return impl_fn(double_ctx)

                    @staticmethod
                    def backward(ctx: Any, *args: Any) -> None:
                        raise RuntimeError(
                            "torch.compile with aot_autograd does not currently support double backward"
                        )

                CompiledFunctionBackward._compiled_autograd_key = (  # type: ignore[method-assign]
                    CompiledFunction._compiled_autograd_key
                )

                return CompiledFunctionBackward.apply(*all_args)

            @staticmethod
            def _backward_impl(ctx: Any, all_args: list[Any]) -> Any:
                # compiled autograd reimplements this function at proxy_call_aot_backward
                if backward_state_indices:
                    raise AssertionError("BackwardState requires CompiledAutograd")
                ctx.maybe_clear_saved_tensors()

                saved_tensors_use_once = (
                    not torch._C._autograd._get_current_graph_task_keep_graph()
                )
                compiled_bw = backward_compiler.get_or_compile(
                    saved_tensors_use_once=saved_tensors_use_once
                )
                CompiledFunction.compiled_bw = compiled_bw

                if (
                    torch._functorch.config.donated_buffer
                    and not saved_tensors_use_once
                    and fw_metadata.bw_donated_idxs != []
                ):
                    torch._check(
                        False,
                        lambda: (
                            "This backward function was compiled with non-empty donated "
                            "buffers which requires create_graph=False and retain_graph=False. "
                            "Please keep backward(create_graph=False, retain_graph=False) "
                            "across all backward() function calls, or set "
                            "torch._functorch.config.donated_buffer=False to disable "
                            "donated buffer."
                        ),
                    )

                return call_func_at_runtime_with_args(
                    compiled_bw,
                    all_args,
                    steal_args=True,
                    disable_amp=disable_amp,
                )

        return CompiledFunction