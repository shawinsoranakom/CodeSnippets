def test_flash_attn_2_inference_equivalence(self):
        dtype = torch.float16

        for model_class in self.all_model_classes:
            if not model_class._supports_flash_attn:
                self.skipTest(f"{model_class.__name__} does not support Flash Attention 2")

            # Prepare inputs
            config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
            if "pixel_values" in inputs_dict:
                inputs_dict["pixel_values"] = inputs_dict["pixel_values"].to(dtype)

            # Separate masks
            attention_masks = {}
            if "attention_mask" in inputs_dict:
                # attention_masks["attention_mask"] = inputs_dict.pop("attention_mask")
                inputs_dict["attention_mask"] = None
            if "pixel_attention_mask" in inputs_dict:
                attention_masks["pixel_attention_mask"] = inputs_dict.pop("pixel_attention_mask")
                inputs_dict["pixel_attention_mask"] = None

            # Save and load model with flash attention 2 and eager attentions
            with tempfile.TemporaryDirectory() as tmp_dir:
                model = model_class(config)
                model.save_pretrained(tmp_dir)

                model = model_class.from_pretrained(tmp_dir, dtype=dtype)
                model_fa = model_class.from_pretrained(tmp_dir, dtype=dtype, attn_implementation="flash_attention_2")

            model_fa.to(torch_device)
            model.to(torch_device)

            # Run forward pass without attention masks
            with torch.no_grad():
                outputs = model(**inputs_dict, output_hidden_states=True)
                outputs_fa = model_fa(**inputs_dict, output_hidden_states=True)

            # Choose which key to compare
            key = [k for k in ["logits", "logits_per_image", "last_hidden_state"] if k in outputs][0]

            torch.testing.assert_close(outputs[key], outputs_fa[key], atol=4e-2, rtol=4e-2)

            # Run forward pass with attention masks
            inputs_dict.update(attention_masks)
            with torch.no_grad():
                outputs = model(**inputs_dict, output_hidden_states=True)
                outputs_fa = model_fa(**inputs_dict, output_hidden_states=True)

            output_tensor = outputs[key]
            output_tensor_fa = outputs_fa[key]

            # Mask out padded tokens, they are different for SDPA and Flash Attention 2
            if key == "last_hidden_state" and "pixel_attention_mask" in inputs_dict:
                output_tensor = output_tensor * inputs_dict["pixel_attention_mask"][..., None]
                output_tensor_fa = output_tensor_fa * inputs_dict["pixel_attention_mask"][..., None]
            elif key == "last_hidden_state" and inputs_dict.get("attention_mask", None) is not None:
                output_tensor = output_tensor * inputs_dict["attention_mask"][..., None]
                output_tensor_fa = output_tensor_fa * inputs_dict["attention_mask"][..., None]

            torch.testing.assert_close(output_tensor, output_tensor_fa, atol=4e-2, rtol=4e-2)

            # Check with inference + dropout
            model.train()
            _ = model_fa(**inputs_dict, output_hidden_states=True)