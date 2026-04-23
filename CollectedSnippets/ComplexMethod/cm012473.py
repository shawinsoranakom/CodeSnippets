def _generate(self, is_inference):
        if config.profile_bandwidth:
            self.write_triton_header_once()

        with contextlib.ExitStack() as stack:
            stack.enter_context(self.wrapper_call.indent())
            if config.profiler_mark_wrapper_call:
                self.generate_profiler_mark_wrapper_call(stack)
            if config.profile_bandwidth:
                self.generate_start_graph()

            self.run_wrapper_ir_passes(is_inference)

            if config.triton.store_cubin and not config.triton.autotune_at_compile_time:
                self.generate_reset_kernel_saved_flags()

            # At this point, we shouldn't generate any new memory planning lines.
            # Override writeline to point at the wrapper call, in case it gets called.
            with self.set_writeline(self.wrapper_call.writeline):
                for line in self.lines:
                    if isinstance(line, WrapperLine):
                        # pyrefly: ignore [missing-attribute]
                        line.codegen(self.wrapper_call)
                    else:
                        self.wrapper_call.writeline(line)

            self._write_multi_kernel_defs()

            output_refs = self.get_output_refs()
            self.mark_output_type()
            if config.triton.debug_sync_graph:
                self.wrapper_call.writeline(V.graph.device_ops.synchronize())

            if config.profile_bandwidth:
                self.generate_end_graph()

            if config.triton.proton_profiling:
                self.generate_proton_finalize()

            if config.triton.store_cubin and not config.triton.autotune_at_compile_time:
                self.generate_save_uncompiled_kernels()

            if config.triton.autotune_at_compile_time:
                self.generate_and_run_autotune_block()

            # cpp_wrapper currently doesn't support nvtx
            if config.annotate_training and not config.cpp_wrapper:
                self.wrapper_call.writeline(
                    "nvtx._device_range_end(training_annotation)"
                )
            self.generate_return(output_refs)

        # Assemble the final code from sections.
        result = IndentedBuffer()
        result.splice(self.imports)
        result.writeline("")
        result.splice(self.header)
        # We do not want the cpp header for intermediate const graph. Headers would be
        # rendered by the main module instead.
        if V.graph.aot_mode and V.graph.cpp_wrapper and V.graph.is_const_graph:
            result = IndentedBuffer()

        # Add subgraph definitions to the result
        result.splice(self.subgraph_definitions)
        self.finalize_prefix()
        result.splice(self.prefix)

        wrapper_call_indent = self.get_wrapper_call_indent()

        with result.indent(wrapper_call_indent):
            result.splice(self.wrapper_call)

        self.generate_before_suffix(result)
        result.splice(self.suffix)
        self.generate_after_suffix(result)

        self.generate_end(result)

        self.add_benchmark_harness(result)

        return (
            result.getvaluewithlinemap(),
            self.kernel_declarations.getvaluewithlinemap(),
        )