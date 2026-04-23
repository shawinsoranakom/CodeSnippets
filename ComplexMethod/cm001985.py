def test_training_step(self, quantized, model, kernels, attn_impl, mode):
        if torch_device == "cpu":
            if attn_impl == "kernels-community/vllm-flash-attn3":
                self.skipTest("vllm-flash-attn3 is not supported on CPU.")
            if kernels and mode == "train":
                self.skipTest("CPU kernels only support inference.")

        if mode != "train":
            self.skipTest("This test is only for training mode.")

        if quantized:
            self.skipTest("Training test for quantized models is not supported.")

        model_id = f"openai/gpt-oss-{model}"

        model_obj = AutoModelForCausalLM.from_pretrained(
            model_id,
            dtype=torch.bfloat16,
            device_map="auto",
            attn_implementation=attn_impl,
            use_kernels=kernels,
        )
        model_obj.train()

        tokenizer = AutoTokenizer.from_pretrained(model_id, padding_side="left")
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        inputs = tokenizer(self.input_text, return_tensors="pt", padding=True).to(model_obj.device)
        inputs["labels"] = inputs["input_ids"].clone()

        outputs = model_obj(**inputs)
        loss = outputs.loss
        self.assertIsNotNone(loss)

        loss.backward()

        # Check that gradients were computed for all parameters that have a grad field
        for name, param in model_obj.named_parameters():
            if param.requires_grad:
                self.assertIsNotNone(param.grad, f"Parameter '{name}' did not receive a gradient.")
                # Check that gradients are not all zero
                self.assertTrue(
                    torch.sum(torch.abs(param.grad)).item() > 0, f"Gradient for parameter '{name}' is all zeros."
                )