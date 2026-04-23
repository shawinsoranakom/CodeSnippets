def create_kernel_choices(  # type: ignore[override]
        self,
        kernel_features: SIMDKernelFeatures,
        kernel_args: list[Any],
        kernel_kwargs: dict[str, Any],
    ) -> list[TritonKernel]:
        is_scan = kernel_features.contains_op("scan")
        is_split_scan = is_scan and any(
            node.is_split_scan() for node in kernel_features.scheduler_nodes()
        )
        kernel_type: type[TritonKernel] = self.kernel_type
        if is_split_scan:
            from .triton_split_scan import TritonSplitScanKernel

            kernel_type = TritonSplitScanKernel

        if is_scan:
            # TODO(jansel): scan does not yet work with cooperative reductions
            kernel_kwargs["override_cooperative_reduction"] = False

        # ops.sort only works with persistent reduction, and is not bandwidth bound anyway
        # so taking the hit of non-coalesced loads is okay
        if kernel_features.contains_op("sort"):
            kernel_kwargs["override_persistent_reduction"] = True
            kernel_kwargs["override_cooperative_reduction"] = False

        if not TritonKernel.has_persistent_RBLOCK(kernel_features.reduction_numel):
            # Cannot use persistent reduction with unknown dynamic rnumel
            assert not kernel_kwargs.get("override_persistent_reduction")
            kernel_kwargs["override_persistent_reduction"] = False

        kernel_kwargs = V.choices.triton_kernel_kwargs(
            kernel_type, kernel_features, kernel_args, kernel_kwargs
        )
        kernel = kernel_type(*kernel_args, **kernel_kwargs)
        return self.add_multi_kernel_choices(kernel, kernel_args, kernel_kwargs)