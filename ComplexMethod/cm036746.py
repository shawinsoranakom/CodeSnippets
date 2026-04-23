def is_valid(self) -> tuple[bool, str | None]:
        # Check prepare-finalize and fused-experts compatibility
        if self.is_batched_prepare_finalize():
            if not self.is_batched_fused_experts():
                return False, "Mismatched format."
        else:
            if not self.is_standard_fused_experts():
                return False, "Mismatched format."

        # Check quantization sanity
        if (
            int(self.is_per_act_token_quant)
            + int(self.is_per_tensor_act_quant)
            + int(self.quant_block_shape is not None)
        ) > 1:
            # invalid quant config
            return False, f"Bad quant_config {self.quant_config}."

        # check type support
        if self.quant_dtype is None:
            if (
                self.dtype not in self.pf_supported_types()
                or self.dtype not in self.fe_supported_types()
            ):
                return False, (
                    f"Unsupported type {self.dtype} not in "
                    f"{self.pf_supported_types()} and "
                    f"{self.fe_supported_types()}."
                )
        else:
            if (
                self.quant_dtype not in self.pf_supported_types()
                or self.quant_dtype not in self.fe_supported_types()
            ):
                return False, (
                    f"Unsupported quant type {self.quant_dtype} "
                    f"not in {self.pf_supported_types()} and "
                    f"{self.fe_supported_types()}."
                )

        # Check quant scheme compatibility with fused experts class
        if not self.fe_supports_quant_scheme():
            return False, (
                f"FE {self.fused_experts_type.__name__} does not support "
                f"quant scheme (per_out_ch={self.is_per_out_ch_quant}, "
                f"per_act_token={self.is_per_act_token_quant}, "
                f"block={self.quant_block_shape})"
            )

        # Check block quantization support
        is_block_quantized = self.quant_block_shape is not None
        if is_block_quantized and self.quant_dtype is None:
            return False, "No block quantization support."

        if is_block_quantized and not self.is_block_quant_supported():
            return False, "Mismatched block quantization support."

        # deep_gemm only works with block-quantized
        if self.needs_deep_gemm() and not is_block_quantized:
            return False, "Needs DeepGEMM but not block quantized."

        # Check dependencies (turn into asserts?)
        if self.needs_deep_ep() and not has_deep_ep():
            return False, "Needs DeepEP, but DeepEP not available."
        if self.needs_deep_gemm() and not has_deep_gemm():
            return False, "Needs DeepGEMM, but DeepGEMM not available."
        if self.needs_aiter() and not has_aiter():  # noqa: SIM103
            return False, "Needs Aiter, but Aiter not available."
        if self.needs_mori() and not has_mori():  # noqa: SIM103
            return False, "Needs MoRI, but MoRI not available."

        return True, None