def test__int4_mm(self, device, m, k, n):
        if self.device_type == 'cuda' and not SM80OrLater:
            self.skipTest("requires SM80 or later")

        if TEST_WITH_ROCM and self.device_type == 'cuda' and not CDNA2OrLater():
            self.skipTest("_convert_weight_to_int4pack_cuda is supported only for CDNA2 or later")

        q_group = 32
        inner_k_tiles = 2

        torch.manual_seed(1)
        a_bf16 = torch.rand((m, k), dtype=torch.bfloat16, device=device)
        b_bf16 = torch.rand((k, n), dtype=torch.bfloat16, device=device)

        def convert_weight_to_int4pack(b):
            b_tmp, b_scales_and_zeros = _group_quantize_tensor(
                b, n_bit=4, q_group_size=q_group
            )
            if self.device_type == 'cpu':
                b_int4pack = torch._convert_weight_to_int4pack_for_cpu(
                    b_tmp, inner_k_tiles
                )
            else:
                b_int4pack = torch._convert_weight_to_int4pack(
                    b_tmp, inner_k_tiles
                )

            return b_int4pack, b_scales_and_zeros

        def weight_int4pack_mm(a, b_int4pack, b_scales_and_zeros):
            if self.device_type == 'cpu':
                self.assertTrue(b_int4pack.dtype is torch.uint8)
                self.assertTrue(b_int4pack.dim() == 2)
                c = torch._weight_int4pack_mm_for_cpu(
                    a, b_int4pack, q_group, b_scales_and_zeros
                )
                # test wrapper
                q_group_t = torch.tensor(q_group, dtype=torch.int64, device=device)
                c_2 = torch.ops.quantized.int4mm_packed_weight_cpu(
                    a, b_int4pack, q_group_t, b_scales_and_zeros
                )
                if not torch.equal(c, c_2):
                    raise AssertionError("c and c_2 should be equal")
                return c
            else:
                self.assertTrue(b_int4pack.dtype is torch.int32)
                self.assertTrue(b_int4pack.dim() == 4)
                return torch._weight_int4pack_mm(
                    a, b_int4pack, q_group, b_scales_and_zeros
                )

        b_int4pack, b_scales_and_zeros_bf16 = convert_weight_to_int4pack(b_bf16)

        for dtype in [torch.bfloat16] + ([torch.float16, torch.float32] if device == "cpu" else []):
            a = a_bf16.to(dtype=dtype)
            b = b_bf16.to(dtype=dtype)
            b_scales_and_zeros = b_scales_and_zeros_bf16.to(dtype=dtype)
            ref = torch.mm(a, b)
            res = weight_int4pack_mm(a, b_int4pack, b_scales_and_zeros)

            mean_err = ((res - ref).abs() / ref).mean()
            self.assertTrue(mean_err < 0.05)