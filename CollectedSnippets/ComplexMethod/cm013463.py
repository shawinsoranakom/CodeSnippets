def _init_modes_from_inputs(
        self, f: Callable[..., Any], args: tuple[object, ...]
    ) -> Generator[None, None, None]:
        prev_modes = self._checkpoint_modes()
        try:
            # Avoid importing sympy at a module level
            from .symbolic_shapes import ShapeEnv

            if hasattr(f, "_orig_mod") and self.record_module_stack:
                scope_root = f._orig_mod
                # _ModuleStackTracer always try to preserve stack trace
                # in forward functions
                self.fx_tracer = _ModuleStackTracer(scope_root)
            else:
                self.fx_tracer = PythonKeyTracer()
                self.fx_tracer.record_stack_traces = (
                    self.record_stack_traces and not fx.config.do_not_emit_stack_traces
                )
                if self.fx_tracer.record_stack_traces:
                    self.fx_tracer._record_forward_stack_traces_only = True

            if self.tracing_mode == "fake":
                import torch._dynamo

                fake_tensor_mode = torch._dynamo.utils.detect_fake_mode(args)
                if fake_tensor_mode is None:
                    import torch._functorch.config as _config

                    with _config.patch(fake_tensor_allow_unsafe_data_ptr_access=False):
                        fake_tensor_mode = FakeTensorMode(
                            allow_fallback_kernels=True,
                            allow_non_fake_inputs=self._allow_non_fake_inputs,
                            shape_env=ShapeEnv(),
                            static_shapes=True,
                        )
                self.fake_tensor_mode = fake_tensor_mode
            elif self.tracing_mode == "symbolic":
                import torch._dynamo

                fake_tensor_mode = torch._dynamo.utils.detect_fake_mode(args)
                if fake_tensor_mode is None:
                    shape_env = ShapeEnv()
                    import torch._functorch.config as _config

                    with _config.patch(fake_tensor_allow_unsafe_data_ptr_access=False):
                        fake_tensor_mode = FakeTensorMode(
                            allow_fallback_kernels=False,
                            allow_non_fake_inputs=self._allow_non_fake_inputs,
                            shape_env=shape_env,
                        )
                if fake_tensor_mode.shape_env is None:
                    raise AssertionError(
                        "shape_env should be set if tracing with 'symbolic'"
                    )
                self.fake_tensor_mode = fake_tensor_mode
            else:
                if not self.tracing_mode == "real":
                    raise AssertionError(
                        f"Unexpected tracing type: {self.tracing_mode}"
                    )

            self._construct_modes_with_fx_tracer(self.fx_tracer)
            yield
        finally:
            self._restore_modes(*prev_modes)