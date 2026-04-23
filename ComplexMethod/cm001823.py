def test_training(self):
        # Step 1: freeze all parameters
        model = AutoModelForCausalLM.from_pretrained(
            self.model_name, quantization_config=BitsAndBytesConfig(load_in_8bit=True)
        )
        model.train()

        if torch_device in ["cuda", "xpu"]:
            hf_device_map = getattr(model, "hf_device_map", None)
            if hf_device_map is not None:
                self.assertEqual(
                    set(hf_device_map.values()), {backend_torch_accelerator_module(torch_device).current_device()}
                )
        else:
            self.assertTrue(all(param.device.type == "cpu" for param in model.parameters()))

        for param in model.parameters():
            param.requires_grad = False  # freeze the model - train adapters later
            # cast all non INT8 parameters to fp32
            if param.dtype in (torch.float16, torch.bfloat16) and param.__class__.__name__ != "Params4bit":
                param.data = param.data.to(torch.float32)

        # Step 2: add adapters
        for _, module in model.named_modules():
            if isinstance(module, OPTAttention):
                module.q_proj = LoRALayer(module.q_proj, rank=16, dtype=model.dtype)
                module.k_proj = LoRALayer(module.k_proj, rank=16, dtype=model.dtype)
                module.v_proj = LoRALayer(module.v_proj, rank=16, dtype=model.dtype)

        # Step 3: dummy batch
        batch = self.tokenizer("Test batch ", return_tensors="pt").to(torch_device)

        # Step 4: Check if the gradient is not None
        with torch.autocast(torch_device):
            out = model.forward(**batch)
            out.logits.norm().backward()

        for module in model.modules():
            if isinstance(module, LoRALayer):
                self.assertTrue(module.adapter[1].weight.grad is not None)
                self.assertTrue(module.adapter[1].weight.grad.norm().item() > 0)
            elif isinstance(module, nn.Embedding):
                self.assertTrue(module.weight.grad is None)