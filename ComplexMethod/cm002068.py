def test_peft_save_reload_preserves_adapter_weights(self):
        """
        Regression test: after save_pretrained + from_pretrained roundtrip, the reloaded model's LoRA
        weights must match the pre-save values. Covers both the encoder and decoder paths.
        """
        from peft import LoraConfig

        cases = [
            (AutoModel, "hf-internal-testing/tiny-random-BertModel"),
            (AutoModelForCausalLM, "hf-internal-testing/tiny-random-OPTForCausalLM"),
        ]
        sentinel_a, sentinel_b = 0.0234, 0.0567

        for auto_class, model_id in cases:
            with self.subTest(model=model_id):
                model = auto_class.from_pretrained(model_id).to(torch_device)
                model.add_adapter(LoraConfig(init_lora_weights=False, r=8))

                with torch.no_grad():
                    for name, p in model.named_parameters():
                        if "lora_A" in name:
                            p.fill_(sentinel_a)
                        elif "lora_B" in name:
                            p.fill_(sentinel_b)

                with tempfile.TemporaryDirectory() as tmpdirname:
                    model.save_pretrained(tmpdirname)
                    reloaded = auto_class.from_pretrained(tmpdirname).to(torch_device)

                lora_params = {
                    name: p for name, p in reloaded.named_parameters() if "lora_A" in name or "lora_B" in name
                }
                self.assertTrue(lora_params, "no LoRA parameters found on reloaded model")
                for name, p in lora_params.items():
                    expected = sentinel_a if "lora_A" in name else sentinel_b
                    self.assertTrue(
                        torch.allclose(p, torch.full_like(p, expected)),
                        f"adapter weight {name} was not restored from the checkpoint "
                        f"(expected uniform {expected}, got first values {p.flatten()[:4].tolist()})",
                    )