def can_use_tma(
        self,
    ) -> bool:
        if self.force:
            return True
        if not (
            (
                (
                    V.graph.get_current_device_or_throw().type == "cuda"
                    and torch.cuda.get_device_capability()[0] >= 9
                    and config.assume_aligned_inputs
                )
                or V.graph.get_current_device_or_throw().type == "xpu"
            )
            and config.triton.use_tensor_descriptor
            and has_triton_stable_tma_api()
            # For CUDA The base ptr needs to be aligned
        ):
            log.debug(
                (
                    "%s Requires triton>=3.4.0, a CUDA device with cc>=9.0 and"
                    " `use_tensor_descriptor` and `assume_aligned_inputs` options enabled"
                ),
                self.failed_debug_prefix,
            )
            return False

        # `no_x_dim` => XBLOCK=1, and for reductions this means only one element
        # is to be stored . However the TMA API requires that
        # the store will be 16 byte aligned, which is not attainable with a single
        # element
        if self.for_store and self.kernel.no_x_dim:
            log.debug(
                "%s stores with `no_x_dim` cannot load 16 bytes.",
                self.failed_debug_prefix,
            )
            return False

        return True