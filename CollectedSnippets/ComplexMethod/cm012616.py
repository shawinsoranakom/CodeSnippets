def add_multi_kernel_choices(
        self,
        kernel: TritonKernel,
        kernel_args: list[Any],
        kernel_kwargs: dict[str, Any],
    ) -> list[TritonKernel]:
        kernels: list[TritonKernel] = [kernel]
        if not config.triton.multi_kernel:
            return kernels

        optional_persistent = kernel.persistent_reduction and not kernel_kwargs.get(
            "override_persistent_reduction"
        )
        optional_cooperative = kernel.cooperative_reduction and not kernel_kwargs.get(
            "override_cooperative_reduction"
        )
        if optional_persistent:
            kernels.append(
                self.kernel_type(
                    *kernel_args,
                    **kernel_kwargs,
                    override_persistent_reduction=False,
                )
            )
        if optional_cooperative:
            rnumel = kernel.features.reduction_numel
            # for larger sizes non-cooperative gets very slow
            if V.graph.sizevars.statically_known_leq(rnumel, 65536):
                kernels.append(
                    other := self.kernel_type(
                        *kernel_args,
                        **kernel_kwargs,
                        override_cooperative_reduction=False,
                    )
                )
                if optional_persistent and other.persistent_reduction:
                    kernels.append(
                        self.kernel_type(
                            *kernel_args,
                            **kernel_kwargs,
                            override_cooperative_reduction=False,
                            override_persistent_reduction=False,
                        )
                    )

        if len(kernels) > 1:
            for kernel2 in kernels[1:]:
                # Keep buffers needed by the non-persistent reduction so both kernels have the same arguments
                kernel2.must_keep_buffers = kernel.must_keep_buffers
            # persistent kernels must be generated last so must_keep_buffers works right
            kernels.sort(key=lambda k: k.persistent_reduction)
        return kernels