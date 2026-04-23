def test_qat_and_script(self):
        model = LinearModelWithSubmodule().train()
        qengine = torch.backends.quantized.engine
        qconfig_dict = {'': torch.ao.quantization.get_default_qat_qconfig(qengine)}
        x = torch.randn(5, 5)
        example_inputs = (x,)
        model = prepare_qat_fx(model, qconfig_dict, example_inputs=example_inputs)

        # ensure scripting works
        scripted = torch.jit.script(model)
        # run one round to make sure model runs
        scripted(x)
        FileCheck().check_count('FakeQuantize = prim::GetAttr[name="', 4, exactly=True) \
                   .run(scripted.graph)

        # disable fake_quant and observer
        for epoch in range(3):
            if epoch == 1:
                scripted.apply(torch.ao.quantization.disable_observer)
            if epoch == 2:
                scripted.apply(torch.ao.quantization.disable_fake_quant)

        # ensure the fake_quant and observer have been disabled.
        matches = ['.fake_quant_enabled', '.observer_enabled']
        for key, v in scripted.state_dict().items():
            if any(x in key for x in matches):
                self.assertEqual(v, torch.tensor([0], dtype=torch.int64))

        # enable them back
        scripted.apply(torch.ao.quantization.enable_fake_quant)
        scripted.apply(torch.ao.quantization.enable_observer)
        for key, v in scripted.state_dict().items():
            if any(x in key for x in matches):
                self.assertEqual(v, torch.tensor([1], dtype=torch.int64))