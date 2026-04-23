def test_qconfig_dict_setup(self):
        class M(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.Conv1d = torch.nn.Conv1d(1, 1, 1)
                self.Conv2d = torch.nn.Conv2d(1, 1, 1)
                self.Conv3d = torch.nn.Conv3d(1, 1, 1)
                self.ConvTranspose1d = torch.nn.ConvTranspose1d(1, 1, 1)
                self.ConvTranspose2d = torch.nn.ConvTranspose2d(1, 1, 1)
                self.ConvTranspose3d = torch.nn.ConvTranspose3d(1, 1, 1)
                self.Linear = torch.nn.Linear(1, 1, 1)

            def forward(self, x):
                x = self.Conv1d(x)
                x = self.Conv2d(x)
                x = self.Conv3d(x)
                x = self.ConvTranspose1d(x)
                x = self.ConvTranspose2d(x)
                x = self.ConvTranspose3d(x)
                x = self.Linear(x)
                x = torch.nn.functional.conv1d(x, torch.rand(2, 2))
                x = torch.nn.functional.conv2d(x, torch.rand(2, 2))
                x = torch.nn.functional.conv3d(x, torch.rand(2, 2))
                x = torch.nn.functional.linear(x, torch.rand(2, 2))
                return x

        backends = ["qnnpack", "fbgemm"]
        for func in [get_default_qconfig_mapping, get_default_qat_qconfig_mapping]:
            for backend in backends:
                m = M().eval()
                qconfig_dict = func(backend)
                m = prepare_fx(m, qconfig_dict, example_inputs=(torch.randn(1, 1, 1, 1)))
                for mod in m.modules():
                    if _is_activation_post_process(mod) and mod.dtype == torch.quint8:
                        if backend == "fbgemm":
                            lower_bnd = 0
                            upper_bnd = 127
                        else:
                            lower_bnd = 0
                            upper_bnd = 255
                        if issubclass(type(mod), FakeQuantize):
                            self.assertEqual(mod.activation_post_process.quant_min, lower_bnd)
                            self.assertEqual(mod.activation_post_process.quant_max, upper_bnd)
                        else:
                            self.assertEqual(mod.quant_min, lower_bnd)
                            self.assertEqual(mod.quant_max, upper_bnd)