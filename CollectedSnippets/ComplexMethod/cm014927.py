def test_native_multihead_self_attention(self, device, dtype, use_nt,
                                             need_weights, average_attn_weights, use_padding, pad_all, fused):
        if TEST_WITH_ROCM:
            if use_nt and use_padding and pad_all:
                self.skipTest("Large numerical errors on ROCM to investigate.")
            if use_padding and not pad_all and fused:
                self.skipTest("Large numerical errors on ROCM to investigate.")
        for need_weights in (False, not pad_all):
            with self.subTest(use_padding=use_padding, pad_all=pad_all,
                              use_nt=use_nt, need_weights=need_weights,
                              average_attn_weights=average_attn_weights):
                sdpa_backends_fused = [
                    SDPBackend.MATH,
                    SDPBackend.OVERRIDEABLE,
                    SDPBackend.CUDNN_ATTENTION,
                    SDPBackend.FLASH_ATTENTION,
                    SDPBackend.EFFICIENT_ATTENTION,
                ]
                sdpa_backends_not_fused = [
                    SDPBackend.MATH,
                    SDPBackend.OVERRIDEABLE,
                    SDPBackend.CUDNN_ATTENTION,
                ]
                if device == "xpu":
                    sdpa_backends_fused = [SDPBackend.OVERRIDEABLE, SDPBackend.MATH]
                    sdpa_backends_not_fused = [SDPBackend.MATH]
                with torch.nn.attention.sdpa_kernel(
                        sdpa_backends_not_fused
                ) if not fused else torch.nn.attention.sdpa_kernel(
                        sdpa_backends_fused
                ):
                    self._test_multihead_attention_impl(
                        device,
                        dtype,
                        "self",
                        use_nt=use_nt,
                        use_padding=use_padding,
                        pad_all=pad_all,
                        need_weights=need_weights,
                        average_attn_weights=average_attn_weights,
                    )