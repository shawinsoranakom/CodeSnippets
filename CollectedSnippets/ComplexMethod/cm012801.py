def _dynamic_scale_rblock(self):
        # TODO(jansel): we should find a way to move this extra compile into the worker process
        # Currently it relies on _make_launchers(), which requires a cuda context, to populate nreg.
        device_prop = self.device_props
        if (
            not self.deterministic_mode
            and self.inductor_meta.get("dynamic_scale_rblock", True)
            and not self.inductor_meta.get("persistent_reduction")
            and self.heuristic_type == HeuristicType.REDUCTION
            and self.size_hints is not None
            # Disable for Intel as Triton is not ready to return n_regs for a compiled_binary.
            and device_prop.type in ["cuda", "hip"]
            and device_prop.major
            and (device_prop.major >= 8 or torch.version.hip)
            and device_prop.regs_per_multiprocessor is not None
        ):
            assert device_prop.regs_per_multiprocessor
            assert device_prop.max_threads_per_multi_processor
            assert device_prop.multi_processor_count
            seen_config_hashes: OrderedSet[Hashable] | None = None
            warp_size = device_prop.warp_size or 32
            for result in self.compile_results:
                triton_config = result.config
                compiled_binary = result.kernel
                assert len(self.size_hints) >= 2
                xblock = triton_config.kwargs.get("XBLOCK", 1)
                reduction_kwargs = [
                    kwarg for kwarg in triton_config.kwargs if kwarg.startswith("R")
                ]
                rblocks = [triton_config.kwargs[kwarg] for kwarg in reduction_kwargs]
                total_block = (self.size_hints["x"] + xblock - 1) // xblock
                nreg = getattr(compiled_binary, "n_regs", None)
                if nreg is None:
                    continue

                # make sure rblocks are not too small
                if conditional_product(*rblocks) <= 64:
                    continue

                # each SM of A100 has 65536 32-bit registers. To maximize
                # the theoretical occupancy, we need run 2048 threads on each
                # SM. So each thread should use no more than 65536 / 2048
                # = 32 registers. In cases where occupancy matters, and each
                # thread uses too many registers, reduce R0_BLOCK to reduce
                # the register usage.
                # For kernel https://gist.github.com/shunting314/e4cccc031fe30d378b9b23c08c238cbd
                # from PLBartForCausalLM, latency improve from
                # 7.795ms to 4.883ms.
                #
                if (
                    nreg
                    <= device_prop.regs_per_multiprocessor
                    // device_prop.max_threads_per_multi_processor
                ):
                    continue

                nreg_per_warp = nreg * warp_size
                nreg_per_block = nreg_per_warp * triton_config.num_warps

                # Previously we set max_blocks_per_sm to 'max_threads_per_multi_processo / (32 * num_warps)'
                # The formula below is a tighter upper bound since we have the assumption that
                #   nreg > device_prop.regs_per_multiprocessor // device_prop.max_threads_per_multi_processor
                # due to the if condition above and:
                #   regs_per_multiprocessor / nreg_per_block
                #   = regs_per_multiprocessor / (nreg * 32 * num_warps)
                #   < regs_per_multiprocessor / ((regs_per_multiprocessor / max_threads_per_multi_processor) * 32 * num_warps)
                #   = max_threads_per_multi_processor / (32 * num_warps)
                # Using a tighter upper bound can reveal more optimization opportunities.
                max_blocks_per_sm = max(
                    device_prop.regs_per_multiprocessor // nreg_per_block, 1
                )

                if total_block <= max_blocks_per_sm * device_prop.multi_processor_count:
                    # no need to improve occupancy
                    continue
                new_config = copy.deepcopy(triton_config)

                # Reduce the largest Rn_BLOCK by a factor of 2.
                largest_rkwarg: str = max(
                    reduction_kwargs, key=triton_config.kwargs.__getitem__
                )
                new_config.kwargs[largest_rkwarg] //= 2

                if seen_config_hashes is None:
                    seen_config_hashes = OrderedSet(
                        [
                            triton_config_to_hashable(x.config)
                            for x in self.compile_results
                        ]
                    )
                new_config_hash = triton_config_to_hashable(new_config)
                if new_config_hash in seen_config_hashes:
                    continue
                seen_config_hashes.add(new_config_hash)
                log.debug(
                    "Dynamically scale down %s from TritonConfig(%s) and get a new TritonConfig(%s)",
                    largest_rkwarg,
                    triton_config,
                    new_config,
                )
                if self.fn.fn is None:
                    """
                    We are in the parent process, while this program was compiled in a worker
                    and the fn was dropped in prepare_for_pickle().  We haven't loaded the module
                    containing the real fn yet.
                    """
                    assert hasattr(self, "_reload_kernel")
                    assert callable(self._reload_kernel)
                    self.fn = self._reload_kernel().fn
                self.compile_results.append(self._precompile_config(new_config))  # noqa: B909

            self._make_launchers()