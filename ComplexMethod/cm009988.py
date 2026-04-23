def get_all(cls) -> list["FwdKernel"]:
        kernels: list[FwdKernel] = []
        for aligned, dtype, (sm, sm_max) in itertools.product(
            [True, False], DTYPES.keys(), SM_RANGES
        ):
            # Remove some kernels we don't use
            if dtype == "bf16" and sm < 80:
                continue
            if not aligned and sm >= 80:
                continue
            for q, k, max_k in [
                (64, 64, 64),
                # We get better perf with 64x128 on A100
                (64 if sm > 75 else 32, 128, 128),
                (32, 128, 2**16),
            ]:
                kernels.append(
                    cls(
                        aligned=aligned,
                        dtype=dtype,
                        sm_range=(sm, sm_max),
                        q=q,
                        k=k,
                        max_k=max_k,
                    )
                )
        return kernels