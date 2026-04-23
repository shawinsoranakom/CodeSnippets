def call_kernel(self, kernel_name):
        """
        Collect the union of arguments from all subkernels as the arguments
        for the multi-kernel.
        """
        # Prevent circular import
        from ..select_algorithm import TritonTemplateKernel

        assert kernel_name == self.kernel_name
        V.graph.wrapper_code.write_triton_header_once()
        _, call_args, _, arg_types = self.kernels[0].args.python_argdefs()
        for kernel in self.kernels[1:]:
            _, other_call_args, _, other_arg_types = kernel.args.python_argdefs()
            assert call_args == other_call_args, (call_args, other_call_args)
            assert arg_types == other_arg_types

        if V.graph.cpp_wrapper and not config.triton.autotune_at_compile_time:
            # for the second pass of cpp-wrapper codegen, we should call
            # the fast kernel directly
            kernel_name = MultiKernelCall.lookup_choice(self.kernel_name)

        if isinstance(self.kernels[0], TritonTemplateKernel) and isinstance(
            self.kernels[0].output_node, MultiTemplateBuffer
        ):
            # For matmuls the grid arguments are passed in as additional arguments
            # to the kernel run method. These grids change based on the various
            # parameters of the matmul. So we need to pass each kernel's grid into
            # the multi call kernel.
            multi_call_args = call_args
            multi_call_arg_types = arg_types
            for kernel in self.kernels:
                additional_call_args, additional_arg_types = (
                    kernel.additional_call_args_and_types()
                )
                multi_call_args.extend(list(additional_call_args))
                multi_call_arg_types.extend(list(additional_arg_types))
        else:
            # numels for all subkernels should be the same. Use kernels[0] here
            self.kernels[0].add_numel_to_call_args(kernel_name, call_args, arg_types)
            multi_call_args = call_args
            multi_call_arg_types = arg_types

        for ws in self.kernels[0].args.workspace_args:
            V.graph.wrapper_code.generate_workspace_allocation(ws)

        if V.graph.cpp_wrapper:
            # We have already selected the best kernel at compile time
            # so we only have one set of call args. NB: this currently
            # doesn't work with MultiTemplateBuffer kernels. @bobrenjc93
            # will add it in a subsequent PR.
            V.graph.wrapper_code.generate_kernel_call(
                kernel_name, call_args, arg_types=arg_types
            )
        else:
            V.graph.wrapper_code.generate_kernel_call(
                kernel_name, multi_call_args, arg_types=multi_call_arg_types
            )

        for ws in reversed(self.kernels[0].args.workspace_args):
            V.graph.wrapper_code.generate_workspace_deallocation(ws)