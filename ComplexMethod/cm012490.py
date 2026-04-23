def define_kernel(
        self,
        kernels: list[Any],
        kernel_shape_keys: list[None | tuple[tuple[int, ...], ...]] | None = None,
    ) -> str:
        """
        Previously we name the multi kernel as "multi_kernel_{kernel_names[0]}".
        This has some minor issue.

        E.g. for persistent reduction https://gist.github.com/shunting314/39e7c00ff8bb2055942ed5a3255d61ca ,
        there are 2 flavors of non-persistent reduction:
          https://gist.github.com/shunting314/056d43d35907e87efb883970b35c17d4
        and
          https://gist.github.com/shunting314/02ee753b65c513c54e695626afe682bd

        The only different is cache eviction policy.

        We should name the multi-kernel differently in these 2 cases.

        kernels:
            A list of kernels
        kernel_shape_keys:
            Specified for size-hint multi-kernels.
            Each list element is a shape key, corresponding to the concrete input & output size hints each kernel was tuned for.
        """
        # Prevent circular import
        from ..select_algorithm import TritonTemplateKernel

        kernel_names = tuple(k.kernel_name for k in kernels)
        if kernel_names in self.subkernel_to_kernel_name:
            return self.subkernel_to_kernel_name[kernel_names]

        # name the multi kernel based on the first kernel
        multi_kernel_name = f"multi_kernel_{len(self.subkernel_to_kernel_name)}"
        self.subkernel_to_kernel_name[kernel_names] = multi_kernel_name

        if V.graph.cpp_wrapper and not config.triton.autotune_at_compile_time:
            # we should not generate any python code for multi-kernel during
            # the second pass of cpp-wrapper.
            return multi_kernel_name

        arg_index: dict[int, list[slice]] = {}
        _, call_args, _, arg_types = kernels[0].args.python_argdefs()
        if isinstance(kernels[0], TritonTemplateKernel) and isinstance(
            kernels[0].output_node, MultiTemplateBuffer
        ):
            for i, kernel in enumerate(kernels):
                additional_call_args, _ = kernel.additional_call_args_and_types()
                if i not in arg_index:
                    arg_index[i] = []
                arg_index[i].append(slice(0, len(call_args)))
                arg_index[i].append(
                    slice(
                        len(call_args) + i * len(additional_call_args),
                        len(call_args) + (i + 1) * len(additional_call_args),
                    )
                )
        else:
            kernels[0].add_numel_to_call_args(multi_kernel_name, call_args, arg_types)
            for i in range(len(kernels)):
                arg_index[i] = [slice(0, len(call_args))]

        keyed_by_sizes = kernel_shape_keys is not None
        buf = self.kernel_defs
        buf.writeline("")
        buf.writeline("arg_index = {")
        for key, slice_list in arg_index.items():
            slice_reprs = ", ".join(repr(s) for s in slice_list)
            buf.writeline(f"    {key}: [{slice_reprs}],")
        buf.writeline("}")

        if not keyed_by_sizes:  # no size hint keys, just call with list of kernels
            buf.writeline(
                f"{multi_kernel_name} = async_compile.multi_kernel({multi_kernel_name!r}, ["
            )
            with buf.indent():
                for name in kernel_names:
                    buf.writeline(f"{name},")
            buf.writeline("], arg_index=arg_index)")
        else:  # call with dict[size hint key, kernel]
            assert isinstance(kernels[0], TritonTemplateKernel)
            assert isinstance(kernel_shape_keys, list)
            assert len(kernels) == len(kernel_shape_keys)
            buf.writeline(
                f"{multi_kernel_name} = async_compile.size_hint_multi_kernel({multi_kernel_name!r}, {{"
            )
            with buf.indent():
                for shape_key, name in zip(kernel_shape_keys, kernel_names):
                    buf.writeline(f"{shape_key}: {name},")
            buf.writeline("}, arg_index=arg_index)")

        if config.triton.autotune_at_compile_time:
            V.graph.wrapper_code.src_to_kernel["\n".join(kernel_names)] = (
                multi_kernel_name
            )

        return multi_kernel_name