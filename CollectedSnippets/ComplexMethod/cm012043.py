def _compile_to_module_lines(
        self, wrapper_code: ValueWithLineMap
    ) -> CompiledModule:
        from .codecache import PyCodeCache

        if config.triton.autotune_at_compile_time:
            # sanitize docstrings in kernel defs (#155006)
            kernel_autotune_defs = self.wrapper_code.kernel_autotune_defs.getvalue()
            kernel_autotune_defs = kernel_autotune_defs.replace('"""', '\\"\\"\\"')

            tuning_code = (
                'r"""\n'
                + "Compile-time auto-tuning block: \n"
                + kernel_autotune_defs
                + self.wrapper_code.kernel_autotune_calls.getvalue()
                + '"""\n'
            )
            wrapper_code.value = tuning_code + wrapper_code.value
        if GraphLowering.save_output_code is not None:
            GraphLowering.save_output_code(wrapper_code.value)
        output_code_log.debug("Output code: \n%s", wrapper_code.value)

        inductor_meta = autotune_cache.inductor_meta_from_config()
        AutotuneCacheBundler.begin_compile(inductor_meta, code=wrapper_code.value)

        try:
            linemap = [
                (line_no, node.stack_trace)  # type: ignore[attr-defined]
                for line_no, node in wrapper_code.line_map
            ]
            key, path = PyCodeCache.write(wrapper_code.value)
            output_code_log.debug("Output code written to: %s", path)

            V.debug.output_code(path)
            V.debug.copy(os.path.splitext(path)[0] + ".debug")
        except Exception:
            trace_structured(
                "inductor_output_code",
                # Just omit the filename, I still want the code though!
                payload_fn=lambda: wrapper_code.value,
            )
            raise
        else:
            trace_structured(
                "inductor_output_code",
                lambda: {
                    "filename": path,
                    "file_path": os.path.abspath(path),
                },
                payload_fn=lambda: wrapper_code.value,
            )
        with dynamo_timed("PyCodeCache.load_by_key_path", log_pt2_compile_event=True):
            mod = PyCodeCache.load_by_key_path(
                key,
                path,
                linemap=linemap,  # type: ignore[arg-type]
                attrs={
                    **self.constants,
                    **self.torchbind_constants,
                    **self.opaque_value_type_classes,
                },
            )
        self.cache_key = key
        self.cache_path = path
        self.cache_linemap = linemap  # type: ignore[assignment]

        if config.benchmark_harness and config.profile_bandwidth_output:
            # run the inputs code gen to get the bandwidth info
            args = mod.get_args()
            mod.benchmark_compiled_module(args, times=1, repeat=1)

        return mod