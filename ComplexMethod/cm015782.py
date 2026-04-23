def test_interpolate_half_pixel(self):
        # testing whether it uses "half_pixel" or "pytorch_half_pixel"
        # see https://github.com/onnx/onnx/blob/main/docs/Operators.md#Resize

        class MyModel(torch.nn.Module):
            def __init__(self, mode, size):
                super().__init__()
                self.mode = mode
                self.size = size

            def forward(self, x):
                return torch.nn.functional.interpolate(
                    x, mode=self.mode, size=self.size
                )

        modes = ["linear", "bicubic"]
        x = [
            torch.randn(1, 2, 6, requires_grad=True),
            torch.randn(1, 2, 4, 6, requires_grad=True),
            torch.randn(1, 2, 4, 4, 6, requires_grad=True),
        ]
        for mode in modes:
            for xi in x:
                mode_i = mode
                if mode == "bicubic" and xi.dim() != 4:
                    continue
                elif mode == "linear":
                    if xi.dim() == 4:
                        mode_i = "bilinear"
                    elif xi.dim() == 5:
                        mode_i = "trilinear"
                for i in range(xi.dim() - 2):
                    size = list(xi.shape[2:])
                    size[i] = 1
                    self.run_test(MyModel(mode_i, size), xi)