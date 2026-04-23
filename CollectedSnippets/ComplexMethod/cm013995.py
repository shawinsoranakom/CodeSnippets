def __call__(self, fn: Any) -> Any:
        # public api for compiler config/options
        def get_compiler_config() -> Any:
            return self.compiler_config

        from .package import DynamoCache

        # If self._package is lazily initialized, we should check the dynamo cache now
        if config.caching_precompile:
            if self._package is not None and not self._package.is_initialized():
                fn_key = fn.forward if isinstance(fn, torch.nn.Module) else fn
                result = DynamoCache.load(fn_key)
                if result is None:
                    # Create a fresh CompilePackage
                    self._package.initialize(fn_key, None, ignore_inlined_sources=False)
                else:
                    try:
                        self._package.initialize(
                            fn_key, result.dynamo, ignore_inlined_sources=False
                        )
                        self._package.install(result.backends)
                    except RuntimeError:
                        log.warning(
                            "Failed to load entry from dynamo cache", exc_info=True
                        )
                        self._package.initialize(
                            fn_key, None, ignore_inlined_sources=False
                        )

        fn = innermost_fn(fn)

        def aot_compile(example_inputs: tuple[tuple[Any, ...], dict[str, Any]]) -> Any:
            from torch._dynamo.aot_compile import aot_compile_fullgraph

            if torch._inductor.config.force_disable_caches:
                raise RuntimeError(
                    "Cannot precompile with torch._inductor.config.force_disable_caches=True; caching is required."
                )

            if not self.fullgraph:
                raise RuntimeError(
                    "Graph breaks are not supported with aot compile. Please use torch.compile(fullgraph=True)."
                )

            if not callable(self.callback):
                raise RuntimeError("aot compile requires a callable dynamo callback.")

            assert self._hooks is not None

            return aot_compile_fullgraph(
                fn,
                example_inputs,
                hooks=self._hooks,
                backend=innermost_backend(self.callback),
                dynamic=self._dynamic,
            )

        # add context containing GraphModule to any GraphModule forward functions
        if isinstance(fn, GraphModule):
            # add context containing GraphModule to any GraphModule forward functions
            code_context.get_context(fn.forward.__code__)["orig_graphmodule"] = (
                weakref.ref(fn)
            )

        # Optimize the forward method of torch.nn.Module object
        if isinstance(fn, torch.nn.Module):
            if type(fn) is torch.jit._script.RecursiveScriptModule:
                raise RuntimeError(
                    "torch.compile does not support compiling torch.jit.script or "
                    "torch.jit.freeze models directly.\n\n"
                    "Workaround: compile the original eager module instead:\n"
                    "  model = torch.nn.Linear(3, 3)\n"
                    "  compiled_model = torch.compile(model)  # compile the eager module\n\n"
                    "torch.jit.script and torch.jit.freeze are deprecated in favor of "
                    "torch.compile. See https://pytorch.org/docs/main/jit.html for details."
                )
            mod = fn
            new_mod = OptimizedModule(mod, self)
            # Save the function pointer to find the original callable while nesting
            # of decorators.
            new_mod._torchdynamo_orig_callable = mod.forward
            new_mod._torchdynamo_wrapper_id = id(new_mod)

            # when compiling torch.nn.Module,
            # provide public api OptimizedModule.get_compiler_config()
            assert not hasattr(new_mod, "get_compiler_config")
            new_mod.get_compiler_config = get_compiler_config

            return new_mod

        if inspect.isclass(fn):
            # User has wrapped the class with compile/disable decorator. Apply
            # disable to init/call method.
            cls_obj = fn
            cls_obj.__call__ = self(cls_obj.__call__)
            if issubclass(cls_obj, torch.nn.Module):
                # NN module variable tracker directly inlines the _call_impl.
                cls_obj._call_impl = self(cls_obj._call_impl)
            return cls_obj

        assert callable(fn), (
            f"A callable function is expected, but {type(fn)} is provided."
        )

        # NOTE [Top-level TorchInGraph and polyfilled functions]
        # Some callables (e.g. torch.exp) are represented as TorchInGraphFunctionVariable
        # when traced inside a frame. When such a function is passed directly to
        # torch.compile, we detect it here so we can force it through wrap_inline.
        # Similarly, functions registered via substitute_in_graph have a polyfill
        # that Dynamo can trace, so they also need wrap_inline.
        from .variables import TorchInGraphFunctionVariable

        rule = trace_rules.lookup(fn)
        top_level_in_graph = isinstance(rule, type) and issubclass(
            rule, TorchInGraphFunctionVariable
        )
        has_polyfill = trace_rules.is_polyfilled_callable(fn)

        try:
            filename = inspect.getsourcefile(fn)
        except TypeError:
            filename = None
        if config.debug_force_nested_calls:
            fn = external_utils.wrap_inline(fn)
        elif config.wrap_top_frame or (
            (
                filename is None
                or trace_rules.check(fn)
                or top_level_in_graph
                or has_polyfill
            )
            and (
                getattr(fn, "__name__", "")
                not in ["_call_impl", "_wrapped_call_impl", "_lazy_forward"]
            )
            and filename not in DONT_WRAP_FILES
        ):
            # call to a builtin without a frame for us to capture
            fn = external_utils.wrap_inline(fn)

        def do_nothing(*arg: Any, **kwargs: Any) -> None:
            pass

        callback: Callable[..., Any] = do_nothing
        if hasattr(self, "callback"):
            callback = self.callback  # type: ignore[assignment]

        is_jit_tracing = torch._C._is_tracing
        is_fx_symbolic_tracing = torch.fx._symbolic_trace.is_fx_symbolic_tracing

        @functools.wraps(fn)
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

        # hooks to properly handle inlining
        if self.error_on_graph_break is not None:
            compile_wrapper._torchdynamo_inline = (  # type: ignore[attr-defined]
                external_utils.wrap_inline_with_error_on_graph_break(
                    fn, self.error_on_graph_break
                )
            )
        else:
            compile_wrapper._torchdynamo_inline = fn  # type: ignore[attr-defined]

        # Save the function pointer to find the original callable while nesting
        # of decorators.
        compile_wrapper._torchdynamo_orig_callable = fn  # type: ignore[attr-defined]
        compile_wrapper._torchdynamo_wrapper_id = id(compile_wrapper)  # type: ignore[attr-defined]

        # when compiling user function instead of nn.Module
        # provide public api _fn.get_compiler_config()
        assert not hasattr(compile_wrapper, "get_compiler_config")
        compile_wrapper.get_compiler_config = get_compiler_config  # type: ignore[attr-defined]
        if torch._dynamo.config.enable_aot_compile:
            compile_wrapper.aot_compile = aot_compile  # type: ignore[attr-defined]

        # If the function is called using torch._dynamo.optimize decorator, we
        # should prevent any type of skipping.
        if callback not in (None, False):
            if not hasattr(fn, "__code__"):
                raise RuntimeError(
                    textwrap.dedent(
                        """

                        torch._dynamo.optimize is called on a non function object.
                        If this is a callable class, please wrap the relevant code into a function and optimize the
                        wrapper function.

                        >> class CallableClass:
                        >>     def __init__(self) -> None:
                        >>         super().__init__()
                        >>         self.relu = torch.nn.ReLU()
                        >>
                        >>     def __call__(self, x):
                        >>         return self.relu(torch.sin(x))
                        >>
                        >>     def print_hello(self):
                        >>         print("Hello world")
                        >>
                        >> mod = CallableClass()

                        If you want to optimize the __call__ function and other code, wrap that up in a function

                        >> def wrapper_fn(x):
                        >>     y = mod(x)
                        >>     return y.sum()

                        and then optimize the wrapper_fn

                        >> opt_wrapper_fn = torch._dynamo.optimize(wrapper_fn)
                        """
                    )
                )
            always_optimize_code_objects[fn.__code__] = True

        return compile_wrapper