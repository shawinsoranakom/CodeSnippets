def gen_ops(self) -> "list[tuple[str, cutlass_gemm_op.GemmOperation]]":  # type: ignore[name-defined]  # noqa: F821
        """
        Creates a list of Cutlass GemmOperation instances that match the operation this template is designed to represent.
        The matching is carried out with respect to the input and output specifications of the operation.

        No function arguments.

        Returns:
            List[tuple[str, cutlass_gemm_op.GemmOperation]]: A list of (cutlass_name, GemmOperation)
            tuples that are compatible with the operation requirements of this template.
        """
        assert cutlass_utils.try_import_cutlass()
        import cutlass_library.gemm_operation as cutlass_gemm_op

        if self.cache_key in self.filtered_ops_cache:
            log.debug("Using cached ops for %s", self.cache_key)
            return self.filtered_ops_cache[self.cache_key]

        with dynamo_timed("CUTLASSGemmTemplate.maybe_fetch_ops"):
            maybe_ops = maybe_fetch_ops(self.device_type)
        if maybe_ops is None:
            log.debug("Cannot fetch ops from cache, generating ops from scratch")
            full_ops = cutlass_utils.gen_ops(self.device_type)
            ops = pytree.tree_flatten(full_ops)[0]
        else:
            log.debug("Using cached ops from cache")
            ops = maybe_ops

        ops = self.global_filter_ops(ops)

        res: dict[str, cutlass_gemm_op.GemmOperation] = {}
        start_time = time.time()
        for op in ops:
            # if changed, need to also change CUTLASS_OPERATION_KIND
            assert isinstance(op, cutlass_gemm_op.GemmOperation)
            filter_res = self.filter_op(op)
            if (
                filter_res is not None
                and res.get(filter_res.configuration_name()) is None
            ):
                res[filter_res.configuration_name()] = filter_res
        log.info(
            "Got cutlass configs: total number of ops: %d. Filtering took %.2f seconds",
            len(res),
            time.time() - start_time,
        )
        sorted_res = sorted(res.items())
        ret_res = sorted_res[: inductor_cutlass_config.cutlass_max_profiling_configs]
        if len(self.filtered_ops_cache) < 50:
            self.filtered_ops_cache[self.cache_key] = ret_res
        else:
            log.debug("Not caching ops since filtered_ops_cache has reached size 50.")
        return ret_res