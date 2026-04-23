def test_qparams_buffers(self):
        class Linear(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.w = torch.ones(5, 5)
                self.b = torch.zeros(5)

            def forward(self, x):
                return torch.nn.functional.linear(x, self.w, self.b)

        class M(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.mods1 = torch.nn.Sequential(
                    Linear(),
                    Linear()
                )
                self.mods2 = Linear()

            def forward(self, x):
                x = self.mods1(x)
                x = self.mods2(x)
                return x

        model = M().eval()
        qconfig_dict = {"": default_qconfig}
        example_inputs = (torch.rand(5, 5),)
        m = prepare_fx(model, qconfig_dict, example_inputs=example_inputs)
        m(*example_inputs)
        m = convert_fx(m)
        keys = m.state_dict().keys()
        quant_scale_count = quant_zero_point = scale_count = zero_point_count = 0
        for k in keys:
            if 'input_scale' in k:
                quant_scale_count = quant_scale_count + 1
            elif 'input_zero_point' in k:
                quant_zero_point = quant_zero_point + 1
            elif 'scale' in k:
                scale_count = scale_count + 1
            elif 'zero_point' in k:
                zero_point_count = zero_point_count + 1

        # Expect each quantized linear op to have a scale and zero point
        self.assertTrue(scale_count == 3, "Expect each quantized linear op to have a scale in state_dict")
        self.assertTrue(zero_point_count == 3, "Expect each quantized linear op to have a zero_point in state_dict")
        m(*example_inputs)
        # ensure it is scriptable
        scripted = torch.jit.script(m)
        scripted_keys = scripted.state_dict().keys()
        scripted.mods1_0_packed_weight_0 = m.state_dict()["mods1_0_packed_weight_0"]
        non_packed_weight_keys = [key for key in keys if "_packed_weight" not in key]
        self.assertTrue(
            set(scripted_keys) == set(non_packed_weight_keys),
            "Expected the scripted model to preserve the state_dict for non-packed weight attributes")
        # TODO: probably don't want to hardcode the attribute names, since they are generated
        for attr_name in [
                "mods1_0_input_scale_0", "mods1_0_input_zero_point_0",
                "mods1_0_scale_1", "mods1_0_zero_point_1",
                "mods1_1_scale_1", "mods1_1_zero_point_1",
                "mods2_scale_1", "mods2_zero_point_1"]:
            self.assertTrue(hasattr(m, attr_name), attr_name + " not found.")