def test_reproduce_121253_issue_addmm_fusion_check(self):
        class Mod(torch.nn.Module):
            def __init__(self, weight, bias, beta, alpha):
                super().__init__()
                self.weight = weight
                self.bias = bias
                self.beta = beta
                self.alpha = alpha

            def forward(self, x):
                return torch.addmm(
                    self.bias, x, self.weight, beta=self.beta, alpha=self.alpha
                )

        dtypes = [torch.float32]
        if torch.ops.mkldnn._is_mkldnn_bf16_supported():
            dtypes.append(torch.bfloat16)
        for dtype in dtypes:
            linear_op = (
                "mkl._mkl_linear"
                if dtype == torch.float32
                else "mkldnn._linear_pointwise"
            )
            for beta, alpha in zip([1.0, 0.1, 0.0], [1.0, 0.1, 1.0]):
                weight = torch.nn.Parameter(torch.randn(64, 64, dtype=dtype))
                bias = torch.nn.Parameter(torch.randn(64, dtype=dtype))
                mod = Mod(weight, bias, beta, alpha).to(dtype).eval()
                with torch.no_grad():
                    x = torch.randn(1, 64, dtype=dtype)
                    include_ops = []
                    exclude_ops = []
                    if (beta != 1.0 and beta != 0.0) or alpha != 1.0:
                        exclude_ops = [linear_op]
                    else:
                        include_ops = [linear_op]
                    self._test_code_common(mod, (x,), include_ops, exclude_ops)