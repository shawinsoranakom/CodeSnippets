def call_kernel(
        self,
        name: str,
        node: "ROCmTemplateBuffer",  # type: ignore[name-defined]
    ) -> None:
        """
        Generates code to call the kernel through V.graph.wrapper_code.
        used from within torch._inductor.wrapper.PythonWrapperCodegen

        name: Name of kernel function.
        node: The ROCmTemplateBuffer node which contains information about the kernel, it's fused epilogue nodes
        as well as all required inputs and outputs.
        """
        wrapper = V.graph.wrapper_code

        arg_types: list[Any]
        if V.graph.cpp_wrapper:
            # Make sure we initialize these kernels since they're exported as
            # C-style symbol names.
            assert isinstance(wrapper, CppWrapperCpu)
            wrapper.initialized_kernels[name] = self
            # Kinda hacky because we always originally initialize name with "KERNEL_NAME"
            # So, we replace with the real kernel name passed as an arg to this function.
            self.signature = self.signature.replace("KERNEL_NAME", name)
            _, call_args, arg_types = self.args.cpp_argdefs(DTYPE_TO_ROCM_TYPE)
        else:
            _, call_args, _, arg_types = self.args.python_argdefs()

        kernel_args = []
        for arg in call_args:
            # dynamo wraps unspec variable as 0d CPU tensor, need convert to scalar
            if V.graph.is_unspec_arg(arg):
                arg = arg + ".item()"
            else:
                if not V.graph.cpp_wrapper:
                    arg = f"c_void_p({arg}.data_ptr())"
            kernel_args.append(arg)

        # add size args
        size_args = [
            f"{V.graph.sizevars.simplify(sarg)}" for sarg in node.template.size_args()
        ]

        if V.graph.cpp_wrapper:
            kernel_args.extend(size_args)
        else:
            kernel_args.extend(f"c_int({sarg})" for sarg in size_args)

        if V.graph.cpp_wrapper:
            arg_types.extend(["int"] * len(node.template.size_args()))

        # the runtime args come right after the size args
        kernel_args.extend(self.runtime_arg_values)
        for arg in self.runtime_arg_info:
            arg_types.append(arg.ty)

        # workspace_size ptr is NULL to mark this call is not intended for retrieving workspace_size.
        # workspace_size should have already been retrieved prior to this call.
        kernel_args.append("nullptr" if V.graph.cpp_wrapper else "None")
        if V.graph.cpp_wrapper:
            arg_types.append("size_t*")

        if node.get_workspace_size() > 0:
            ws = WorkspaceArg(
                count=node.get_workspace_size(),
                device=V.graph.get_current_device_or_throw(),
                zero_mode=WorkspaceZeroMode.UNINITIALIZED,
                outer_name=WorkspaceArg.unique_name(),
            )
            wrapper.generate_workspace_allocation(ws)
            data_ptr = f"{ws.outer_name}.data_ptr()"
            kernel_args.append(
                data_ptr if V.graph.cpp_wrapper else f"c_void_p({data_ptr})"
            )
        else:
            ws = None
            kernel_args.append("nullptr" if V.graph.cpp_wrapper else "None")
        if V.graph.cpp_wrapper:
            arg_types.append("uint8_t*")
        wrapper.generate_kernel_call(
            name,
            kernel_args,
            triton=False,
            arg_types=arg_types,
        )
        if ws:
            wrapper.generate_workspace_deallocation(ws)