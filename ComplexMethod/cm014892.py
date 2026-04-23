def _compute_tolerances(self, op, dtype):
        if (op.name in self.FP32_LOW_PRECISION_LIST) and dtype in [torch.float32, torch.complex64]:
            return (1e-4, 3e-5)

        if op.name in self.FP16_LOW_PRECISION_LIST and dtype in [torch.float16, torch.bfloat16]:
            return (2e-2, 1e-2) if dtype == torch.float16 else (5e-2, 5e-2)

        if op.name in self.BF16_LOW_PRECISION_LIST and dtype == torch.bfloat16:
            return (5e-2, 5e-2)

        if op.name in ['nn.functional.conv_transpose1d',
                       'nn.functional.conv_transpose2d',
                       'nn.functional.conv_transpose3d',
                       '__rmatmul__', 'addbmm', 'addmm', 'addmv',
                       'baddbmm', 'corrcoef', 'cov', 'linalg.multi_dot',
                       'matmul', 'mv',
                       'nn.functional.linear'] and dtype in [torch.float16, torch.bfloat16]:
            return (5e-2, 5e-2) if dtype == torch.float16 else (5e-2, 1e-1)
        if op.name == "masked.mean":
            return (7e-4, 2e-3)
        if op.name == "native_layer_norm":
            return (1e-4, 1.3e-5)
        if op.name in ['fft.rfftn', 'fft.hfftn', 'fft.hfft2', 'fft.fft', 'fft.fftn', 'fft.rfft']:
            # TODO: Investigate why this is needed
            # See https://github.com/pytorch/pytorch/issues/120237
            return (3e-5, 3e-5)
        # TODO: Rounding is broken for linspace, see https://github.com/pytorch/pytorch/issues/137635
        if op.name == 'linspace' and dtype in [torch.int8, torch.uint8, torch.int32, torch.int16, torch.int64]:
            return (1.0, 0.0)
        if op.name == "index_reduce" and op.variant_test_name in ['mean', 'prod'] and dtype in [torch.float16, torch.bfloat16]:
            return (0.01, 0.01)
        return (None, None)