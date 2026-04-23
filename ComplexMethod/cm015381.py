def test_nccl_heuristics(self):
        if len(baseLat) != len(NCCL_ALGO):
            raise AssertionError(
                f"Expected len(baseLat) == len(NCCL_ALGO), got {len(baseLat)} vs {len(NCCL_ALGO)}"
            )
        if not all(len(x) == len(NCCL_PROTO) for x in baseLat):
            raise AssertionError(
                "Expected all elements in baseLat to have len(NCCL_PROTO)"
            )

        if len(hwLat) != len(NCCL_HW):
            raise AssertionError(
                f"Expected len(hwLat) == len(NCCL_HW), got {len(hwLat)} vs {len(NCCL_HW)}"
            )
        if not all(len(x) == len(NCCL_ALGO) for x in hwLat):
            raise AssertionError(
                "Expected all elements in hwLat to have len(NCCL_ALGO)"
            )
        if not all(len(y) == len(NCCL_PROTO) for x in hwLat for y in x):
            raise AssertionError(
                "Expected all nested elements in hwLat to have len(NCCL_PROTO)"
            )

        if len(llMaxBws) != len(NVIDIA_GPU_TYPE):
            raise AssertionError(
                f"Expected len(llMaxBws) == len(NVIDIA_GPU_TYPE), got {len(llMaxBws)} vs {len(NVIDIA_GPU_TYPE)}"
            )