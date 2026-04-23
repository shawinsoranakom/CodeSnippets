def test_init_zero3(self, dtype):
        if dtype == "fp16" and not is_torch_fp16_available_on_device(torch_device):
            self.skipTest("test requires fp16 hardware support")
        if dtype == "bf16" and not is_torch_bf16_available_on_device(torch_device):
            self.skipTest("test requires bf16 hardware support")

        extra = {dtype: {"enabled": True}} if dtype in ("fp16", "bf16") else None
        model = self._check_zero3_init_and_removal(extra)

        # ZeRO-3 is the only stage that casts model weights to fp16/bf16 via zero.Init().
        # ZeRO-2/1 keep the model in its original dtype (fp32) and create half-precision
        # copies for forward/backward, meaning both fp32 and fp16/bf16 coexist in memory.
        if dtype == "fp16":
            expected_dtype = torch.float16
        elif dtype == "bf16":
            expected_dtype = torch.bfloat16
        else:
            expected_dtype = torch.float32

        for name, param in model.named_parameters():
            self.assertEqual(
                param.dtype, expected_dtype, f"Parameter {name} has dtype {param.dtype}, expected {expected_dtype}"
            )