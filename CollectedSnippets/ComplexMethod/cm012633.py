def generate(self, wrapper: CppWrapperGpu):
        """
        Generate the GPU kernel definition, as well as load and launch code.
        """
        prefix = wrapper.prefix
        if self.kernel_name.startswith("multi_kernel_"):
            # MultiKernel will select one kernel after running the autotune block
            self.kernel_name = MultiKernelCall.lookup_choice(self.kernel_name)

        # Defer compilation to runtime if autotune_at_compile_time is False (JIT only)
        if not V.graph.aot_mode and config.triton.autotune_at_compile_time is False:
            return self.generate_lazy(wrapper)

        params = CudaKernelParamCache.get(self.kernel_name)
        assert params, f"CudaKernelParamCache not populated for {self.kernel_name}"
        def_args = params["def_args"]
        arg_types = self.arg_types
        inductor_meta = params["inductor_meta"]

        if "extra_launcher_args" in inductor_meta and len(def_args) > len(arg_types):
            # extra_launcher_args should already be in def_args
            assert len(def_args) == len(arg_types) - len(
                inductor_meta["extra_launcher_args"]
            )
            arg_types = arg_types + [SymbolicCallArg] * len(
                inductor_meta["extra_launcher_args"]
            )

        if not V.graph.aot_mode:
            prefix.writeline(
                maybe_hipify_code_wrapper(
                    f"static {wrapper.device_codegen.cpp_kernel_type()} {self.kernel_name} = nullptr;"
                )
            )
            kernel_var_name = self.kernel_name
        else:
            kernel_var_name = f"kernels_.{self.kernel_name}"

        # Write wrapper function signature
        self._write_wrapper_signature(prefix, wrapper, def_args, arg_types)

        with prefix.indent():
            if V.graph.aot_mode:
                # Emit the original Triton kernel for debugging purposes
                prefix.writeline("/*")
                prefix.splice(self.kernel_name_to_body[self.kernel_name])
                prefix.writeline("*/")
            self.generate_grid(prefix, inductor_meta, params)
            self.generate_load_kernel(prefix, kernel_var_name, params)
            self.generate_launch_kernel(prefix, wrapper, kernel_var_name, params)
        prefix.writeline("}")

        if not config.aot_inductor.embed_kernel_binary:
            # Ensure the cubin file is included in the package
            V.graph.wrapper_code.additional_files.append(
                params[get_cpp_wrapper_cubin_path_name()]
            )