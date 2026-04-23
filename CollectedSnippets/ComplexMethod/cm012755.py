def gen_ops(self) -> list[InductorROCmOp]:
        """
        Creates a list of `CKGemmOperation` instances that match the GEMM operation this template represents.
        The instances are guaranteed to have the correct layout, dtype and dimension padding for the GEMM input arguments.

        An instance may invalidate the GEMM configuration at runtime.
        Such instances will be assigned +inf runtime by the autotune process.
        """
        try:
            from ck4inductor.batched_universal_gemm.gen_instances import (  # type: ignore[import]
                gen_ops_library as gen_batched_gemm_ops_library,
            )
            from ck4inductor.universal_gemm.gen_instances import (  # type: ignore[import]
                gen_ops_library as gen_gemm_ops_library,
                gen_ops_preselected as gen_gemm_ops_preselected,
            )
        except ImportError:
            return []

        generator = None
        if self.is_batched:
            generator = gen_batched_gemm_ops_library
        else:
            generator = gen_gemm_ops_library
        if config.rocm.use_preselected_instances and self._is_rcr_f16():
            generator = gen_gemm_ops_preselected

        assert generator is not None

        rops = generator()
        ops = []
        for o in rops:
            kBatches = self._get_kBatch(o)
            for kBatch in kBatches:
                # pyrefly: ignore [bad-argument-type]
                ops.append(InductorROCmOp(op=o, kBatch=kBatch))

        filtered_instances = list(filter(lambda op: self.filter_op(op), ops))

        # NB: when using a fixed list order, most likely we will pick the subset of instances
        # which are very similar to each other. Randomizing the choice seems to solve this.
        random.seed(-11)
        chosen_instances = (
            random.sample(
                filtered_instances,
                min(len(filtered_instances), config.rocm.ck_max_profiling_configs),
            )
            if config.rocm.ck_max_profiling_configs
            else filtered_instances
        )
        log.debug(
            "generated %d ck instances after filter: %s",
            len(chosen_instances),
            chosen_instances,
        )
        return chosen_instances