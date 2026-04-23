def call_kernel(
        self,
        name: str,
        node: "CUTLASSTemplateBuffer",  # type: ignore[name-defined]
    ) -> None:
        """
        Generates code to call the kernel through V.graph.wrapper_code.
        used from within torch._inductor.wrapper.PythonWrapperCodegen

        name: Name of kernel function.
        node: The CUTLASSTemplateBuffer node which contains information about the kernel, it's fused epilogue nodes
        as well as all required inputs and outputs.
        """
        wrapper = V.graph.wrapper_code

        arg_types: list[Any]
        if V.graph.cpp_wrapper:
            # Make sure we initialize these kernels since they're exported as
            # C-style symbol names.
            assert isinstance(wrapper, CppWrapperCpu)
            wrapper.initialized_kernels[name] = self
            # We always originally initialize name with "KERNEL_NAME". So, we
            # we replace with the real kernel name passed as an arg to this function.
            self.signature = self.signature.replace(str(Placeholder.KERNEL_NAME), name)
            _, call_args, arg_types = self.args.cpp_argdefs(DTYPE_TO_CUTLASS_TYPE)
        else:
            _, call_args, _, arg_types = self.args.python_argdefs()

        dynamic_shape_args = self.get_dynamic_shape_args()
        offset_args = self.get_offset_args()
        call_args.extend(dynamic_shape_args)  # type: ignore[arg-type]
        call_args.extend(offset_args)  # type: ignore[arg-type]
        for arg in self.runtime_arg_values:
            call_args.append(str(arg))
        arg_types.extend("const int" for _ in dynamic_shape_args)
        arg_types.extend("const int" for _ in offset_args)
        for arg in self.runtime_arg_info:
            arg_types.append(arg.ty)
        # dynamo wraps unspec variable as 0d CPU tensor, need convert to scalar
        for i in range(len(call_args)):
            if V.graph.is_unspec_arg(call_args[i]):
                call_args[i] = call_args[i] + ".item()"
            elif isinstance(arg_types[i], torch_dtype):
                call_args[i] = (
                    call_args[i]
                    if V.graph.cpp_wrapper
                    else f"c_void_p({call_args[i]}.data_ptr())"
                )

        # workspace_size ptr is NULL to mark this call is not intended for retrieving workspace_size.
        # workspace_size should have already been retrieved prior to this call.
        # workspace_size is here.
        call_args.append("nullptr" if V.graph.cpp_wrapper else "None")
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
            workspace = str(ws.outer_name)
            call_args.append(
                workspace
                if V.graph.cpp_wrapper
                else f"c_void_p({workspace}.data_ptr())"
            )
        else:
            ws = None
            call_args.append("nullptr" if V.graph.cpp_wrapper else "None")
        if V.graph.cpp_wrapper:
            arg_types.append("uint8_t*")

        wrapper.generate_kernel_call(
            name,
            call_args,
            triton=False,
            arg_types=arg_types,
        )
        if ws:
            wrapper.generate_workspace_deallocation(ws)