def codegen_with_cpp_wrapper(
        self,
    ) -> tuple[ValueWithLineMap, ValueWithLineMap]:
        """
        For GPU, Triton kernels are autotuned and stored as cubin files
        """
        if any(device in self.device_types for device in ["cuda", "xpu"]):

            def extract_real_inputs() -> list[int | float | torch.Tensor]:
                def materialize(
                    x: torch.SymInt | torch.SymFloat | torch.Tensor,
                ) -> int | float | torch.Tensor:
                    if x is None:
                        # pyrefly: ignore [bad-return]
                        return None
                    elif isinstance(x, (torch.SymInt, torch.SymFloat)):
                        # Need concrete value to run dynamic shapes and tune the result
                        return x.node.hint
                    elif isinstance(x, FakeTensor):
                        return defake(x)
                    else:
                        assert isinstance(x, torch.Tensor), (
                            "Unknown type when creating real inputs" + str(type(x))
                        )
                        return x

                tracing_context = torch._guards.TracingContext.try_get()
                if tracing_context is not None and not isinstance(
                    V.real_inputs, NullHandler
                ):
                    if tracing_context.output_strides:
                        tracing_context.output_strides.clear()

                    params_flat = [
                        param
                        for param in tracing_context.params_flat  # type: ignore[union-attr]
                        if param is not None
                    ]
                    real_inputs = [
                        materialize(x)
                        for x in itertools.chain(params_flat, V.real_inputs)
                    ]
                else:
                    # In the backward pass, V.real_inputs is not OrderedSet.
                    # Generating random inputs based on self.example_inputs sometimes can be problematic,
                    # e.g. illegal memory access. A comprehensive fix is to autotune in a separate process.
                    real_inputs = [
                        materialize(x)  # type:ignore[arg-type]
                        for x in (
                            self.example_inputs  # type:ignore[union-attr]
                            if isinstance(V.real_inputs, NullHandler)
                            else V.real_inputs
                        )
                    ]

                if self.mutated_inputs:
                    from .compile_fx import clone_preserve_strides

                    mutated_input_idxs = [
                        idx
                        for idx, name in enumerate(self.graph_inputs)
                        if name in self.mutated_inputs
                        and isinstance(real_inputs[idx], torch.Tensor)
                    ]
                    for idx in mutated_input_idxs:
                        # clone mutated Tensor inputs to avoid mutating them in
                        # the first pass of the CPP wrapper-based compilation, as
                        # this will lead to a side effect on the example inputs:
                        # e.g. if torch.compile(f)(x) if called on input-mutating
                        # f, the inputs x will be mutated twice in the process:
                        # once here, and again when running the compiled model;
                        # this will also lead to a numerically incorrect output
                        mutated_inp = real_inputs[idx]
                        assert isinstance(mutated_inp, torch.Tensor)
                        real_inputs[idx] = clone_preserve_strides(mutated_inp)
                        del mutated_inp
                return real_inputs

            if config.triton.autotune_at_compile_time:
                # If autotune_at_compile_time is True, we can do the codegen in one-pass
                # We will construct the autotuning values if user defined kernel exists.
                if config.triton.autotune_with_sample_inputs:
                    user_defined_kernels = False
                    for op in self.operations:
                        if isinstance(op, ir.UserDefinedTritonKernel):
                            user_defined_kernels = True
                            break
                    if user_defined_kernels:
                        real_inputs = extract_real_inputs()
                        self.extract_autotune_inputs(real_inputs)
                        save_triton_kernel_perf_artifact(self)
                return self.codegen()
            else:
                if not self.aot_mode:
                    # Lazy kernel compilation does not require two passes
                    # TODO: need to consolidate the logic between AOT and JIT
                    return self.codegen()

                # first pass
                self.cpp_wrapper = False
                compiled = self.compile_to_module().call

                real_inputs = extract_real_inputs()
                with torch.utils._python_dispatch._disable_current_modes():
                    compiled(real_inputs)
                del real_inputs

                # second pass
                self.cpp_wrapper = True
                self.removed_buffers.clear()
                self.removed_operations.clear()
                self.inplaced_to_remove.clear()
                V.graph.sizevars.precomputed_replacements.clear()
                V.graph.sizevars.inv_precomputed_replacements.clear()
                metrics.reset()
                with config.patch({"triton.autotune_at_compile_time": False}):
                    return self.codegen()
        else:
            # cpu
            return self.codegen()