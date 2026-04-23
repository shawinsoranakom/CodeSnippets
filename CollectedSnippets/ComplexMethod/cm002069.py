def test_peft_load_adapter_training_inference_mode_false(self):
        """
        When passing is_trainable=True, the LoRA modules should be in training mode and their parameters should have
        requires_grad=True.
        """
        for model_id in self.peft_test_model_ids:
            for transformers_class in self.transformers_test_model_classes:
                peft_model = transformers_class.from_pretrained(model_id, use_safetensors=False).to(torch_device)

                with tempfile.TemporaryDirectory() as tmpdirname:
                    peft_model.save_pretrained(tmpdirname)
                    model = transformers_class.from_pretrained(peft_model.config._name_or_path)
                    model.load_adapter(tmpdirname, is_trainable=True)

                    for name, module in model.named_modules():
                        if list(module.children()):
                            # only check leaf modules
                            continue

                        if "lora_" in name:
                            assert module.training
                            assert all(p.requires_grad for p in module.parameters())
                        else:
                            assert not module.training
                            assert all(not p.requires_grad for p in module.parameters())