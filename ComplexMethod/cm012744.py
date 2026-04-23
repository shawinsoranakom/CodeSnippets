def _dynamic_cluster_block(self, op: "cutlass_gemm_op.GemmOperation") -> str:  # type: ignore[name-defined]  # noqa: F821
        """
        Temporary workaround for CUTLASS GEMMs that encode cluster shape as runtime values.

        For dynamic-cluster kernels, CUTLASS expects `KernelHardwareInfo.cluster_shape` and
        `KernelHardwareInfo.cluster_shape_fallback` to be populated with valid runtime values.
        Today we provide a single global preferred/fallback pair (configurable via env),
        which is sufficient for correctness but is not performance-optimal.

        Note: This is intentionally minimal because this code path is transitional. Cluster-shape
        selection should ultimately be handled in the CuTe/DSL implementation rather than
        investing heavily in the legacy CUTLASS template pipeline.
        """
        shape = getattr(getattr(op, "tile_description", None), "cluster_shape", None)
        if not shape or len(shape) < 2 or (shape[0] > 0 and shape[1] > 0):
            return ""

        preferred = inductor_cutlass_config.cutlass_dynamic_cluster_shape
        fallback = inductor_cutlass_config.cutlass_dynamic_cluster_fallback

        cluster_k = shape[2] if len(shape) > 2 and shape[2] > 0 else preferred[2]
        preferred = (preferred[0], preferred[1], cluster_k)
        fallback_k = fallback[2] if len(fallback) > 2 and fallback[2] > 0 else cluster_k
        fallback = (fallback[0], fallback[1], fallback_k)

        return (
            f"  hw_info.cluster_shape = {{{preferred[0]}, {preferred[1]}, {preferred[2]}}};\n"
            f"  hw_info.cluster_shape_fallback = {{{fallback[0]}, {fallback[1]}, {fallback[2]}}};"
        )