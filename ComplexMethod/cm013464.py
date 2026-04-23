def _trace_inner(self, f: Callable[..., Any], *args: object) -> GraphModule:
        # TODO: We need to explicitly import torch._dynamo before calling dispatch_trace,
        # because dispatch_trace will introduce the lazy import of torch._dynamo,
        # and some contexts set before calling dispatch_trace will cause problems with the import of torch._dynamo,
        # such as some torch API(torch.ones and so on) in populate_builtin_to_tensor_fn_map() will be affected
        # by the context set before dispatch_trace.
        import torch._dynamo

        phs = pytree.tree_map(lambda _: torch.fx._symbolic_trace.PH, args)

        args = self._convert_args_to_fake(args)

        # FX doesn't support varargs, so we gotta fake up a wrapper
        # TODO: Would be nice to fix this at the source...
        func: Callable[..., Any] = f
        if (
            not hasattr(inspect.unwrap(f), "__code__")
            or inspect.unwrap(f).__code__.co_flags & inspect.CO_VARARGS
        ):
            func = fake_signature(f, len(phs))
        # We disable the autocast cache as the autocast cache causes type conversions on parameters to
        # check a cache, which introduces untracked tensors into the graph
        #
        # We also disable tracing by any other tensor proxy-based tracers except the current. The
        # purpose of `make_fx` is to produce graphmodules as a side effect; its internal execution is
        # thus irrelevant to any external functional trace.
        proxy_mode: ProxyTorchDispatchMode = typing.cast(
            ProxyTorchDispatchMode, self.proxy_mode
        )
        with ExitStack() as stack:
            stack.enter_context(decompose(self.decomposition_table))
            if self.fake_tensor_mode:
                stack.enter_context(self.fake_tensor_mode)
            stack.enter_context(self.python_dispatcher_mode)
            stack.enter_context(self.proxy_function_mode)
            stack.enter_context(self.torch_fn_metadata_mode)
            stack.enter_context(proxy_mode)
            stack.enter_context(disable_autocast_cache())
            stack.enter_context(_set_make_fx_tracer(self))

            if self.fx_tracer is None:
                raise AssertionError("fx_tracer should not be None")
            try:
                t = dispatch_trace(
                    wrap_key(func, args, self.fx_tracer, self.pre_dispatch),
                    tracer=self.fx_tracer,
                    concrete_args=tuple(phs),
                )
            except Exception:
                trace_structured(
                    "artifact",
                    metadata_fn=lambda: {
                        "name": "make_fx_fail_partial",
                        "encoding": "string",
                    },
                    payload_fn=lambda: self.fx_tracer.graph.python_code(  # type: ignore[union-attr]
                        root_module="self",
                        verbose=True,
                        include_stride=True,
                        include_device=True,
                    ).src,
                )
                raise

        if (
            self.is_hop_subgraph_tracer()
            and (fake_mode := torch._guards.detect_fake_mode(args))
            and fake_mode.shape_env is not None
        ):
            from torch.fx.passes.runtime_assert import insert_deferred_runtime_asserts

            insert_deferred_runtime_asserts(t, fake_mode.shape_env, "reenter_make_fx")
            t.recompile()
        # TODO: kind of a bad way to do it, should maybe figure out a better way
        if self.tracing_mode == "symbolic":
            if self.fake_tensor_mode is None:
                raise AssertionError("fake_tensor_mode should not be None")
            t.shape_env = self.fake_tensor_mode.shape_env  # type: ignore[assignment]
        return t