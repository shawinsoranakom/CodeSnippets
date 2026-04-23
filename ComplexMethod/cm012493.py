def can_fuse_vertical(
        self, node1: BaseSchedulerNode, node2: BaseSchedulerNode
    ) -> bool:
        if self._cutlass_scheduling.can_fuse_vertical(node1, node2):
            return True
        elif self._cutlass_scheduling.is_cutlass_template(
            node1
        ) or self._cutlass_scheduling.is_cutlass_template(node2):
            return False
        # CuteDSL doesn't support vertical fusion currently
        elif self._cutedsl_scheduling.is_cutedsl_template(
            node1
        ) or self._cutedsl_scheduling.is_cutedsl_template(node2):
            return False
        # NVIDIA Universal GEMM doesn't support vertical fusion currently
        elif self._nv_universal_gemm_scheduling.is_nv_universal_gemm_template(
            node1
        ) or self._nv_universal_gemm_scheduling.is_nv_universal_gemm_template(node2):
            return False
        return self._triton_scheduling.can_fuse_vertical(node1, node2)