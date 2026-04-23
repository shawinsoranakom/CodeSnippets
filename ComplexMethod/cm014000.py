def compile_wrapper(*args: Any, **kwargs: Any) -> Any:
            # NB: function calls here could change global state (e.g. random state)
            # and that can result in different behavior between eager and compiled!
            # In particular, we don't have control over internal functions like justknobs_check
            # called in _maybe_set_eval_frame.
            # Unlike in eval_frame_cpp.cpp/convert_frame.py, we don't attempt to restore global state
            # due to additional overhead costs.
            prior = set_eval_frame(None)
            prior_error_on_nested_compile: bool | None = None
            fullgraph_count_enabled = False
            if self.fullgraph:
                prior_error_on_nested_compile = set_fullgraph_error_on_nested_compile(
                    torch._dynamo.config.error_on_dynamo_callback_in_fullgraph_compiled_code
                )
                if not self.export:
                    fullgraph_count_enabled = set_fullgraph_compiled_frame_count(0) < 0
            try:
                # We shouldn't compile inside kernel invocation.
                if tracing_context := torch._guards.TracingContext.try_get():
                    if (
                        tracing_context.fake_mode is not None
                        and tracing_context.fake_mode.in_kernel_invocation
                    ):
                        return fn(*args, **kwargs)
                # Skip nested compile during export (but not HOP internal compile)
                # Only skip if there's an active TracingContext (nested), not for top-level export
                if (
                    torch.compiler.is_exporting()
                    and not config.force_compile_during_fx_trace
                ):
                    from torch._higher_order_ops.utils import _in_hop_compile

                    if not _in_hop_compile():
                        if torch._guards.TracingContext.try_get() is not None:
                            return fn(*args, **kwargs)
                # Skip nested compile - just inline the function
                if (
                    is_fx_symbolic_tracing()
                    and not config.force_compile_during_fx_trace
                ):
                    if config.error_on_nested_fx_trace:
                        raise RuntimeError(
                            "Detected that you are using FX to symbolically trace "
                            "a dynamo-optimized function. This is not supported at the moment."
                        )
                    else:
                        return fn(*args, **kwargs)

                if is_jit_tracing():
                    raise RuntimeError(
                        "Detected that you are using FX to torch.jit.trace "
                        "a dynamo-optimized function. This is not supported at the moment."
                    )

                cleanups = [enter() for enter in self.enter_exit_hooks]
                prior_skip_guard_eval_unsafe = set_skip_guard_eval_unsafe(
                    _is_skip_guard_eval_unsafe_stance()
                )
                prior_error_on_graph_break = None
                if not self.fullgraph and self.error_on_graph_break is not None:
                    prior_error_on_graph_break = _get_error_on_graph_break()
                    _set_error_on_graph_break(self.error_on_graph_break)

                # Ensure that if an assertion occurs after graph pushes
                # something onto the DynamicLayerStack then we pop it off (the
                # constructed graph code isn't guarded with try/finally).
                #
                # This used to be a context but putting a `with` here is a noticeable
                # perf regression (#126293)
                saved_dynamic_layer_stack_depth = (
                    torch._C._functorch.get_dynamic_layer_stack_depth()
                )

                _maybe_set_eval_frame(_callback_from_stance(callback))

                call_succeeded = False
                try:
                    result = fn(*args, **kwargs)
                    call_succeeded = True
                except (Unsupported, UncapturedHigherOrderOpError, UserError) as e:
                    if config.verbose:
                        raise
                    # strip internal tracebacks from causes
                    cur_exn: BaseException = e
                    while cur_exn.__cause__ is not None:
                        cur_exn.__cause__.with_traceback(None)
                        cur_exn = cur_exn.__cause__

                    raise e.with_traceback(None) from e.__cause__  # User compiler error
                except ShortenTraceback as e:
                    # Failures in the backend likely don't have useful
                    # data in the TorchDynamo frames, so we strip them out.
                    raise e.remove_dynamo_frames() from None  # see TORCHDYNAMO_VERBOSE=1
                finally:
                    # Restore the dynamic layer stack depth if necessary.
                    set_eval_frame(None)
                    if fullgraph_count_enabled and call_succeeded:
                        count = set_fullgraph_compiled_frame_count(-1)
                        if count == 0:
                            raise RuntimeError(
                                "torch.compile with fullgraph=True found no compiled frames. "
                                "The frame was likely skipped (e.g., a non-infra torch dispatch "
                                "mode was active, dynamo was disabled, or the frame was skipped."
                            )
                    if prior_error_on_graph_break is not None:
                        _set_error_on_graph_break(prior_error_on_graph_break)
                    if prior_error_on_nested_compile is not None:
                        set_fullgraph_error_on_nested_compile(
                            prior_error_on_nested_compile
                        )
                    torch._C._functorch.pop_dynamic_layer_stack_and_undo_to_depth(
                        saved_dynamic_layer_stack_depth
                    )

                    set_skip_guard_eval_unsafe(prior_skip_guard_eval_unsafe)
                    for cleanup in cleanups:
                        cleanup()
                return result
            finally:
                if fullgraph_count_enabled:
                    set_fullgraph_compiled_frame_count(-1)
                _maybe_set_eval_frame(prior)