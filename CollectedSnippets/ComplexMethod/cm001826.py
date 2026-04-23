def test_serialization(self, quant_type="nf4", double_quant=True):
        r"""
        Test whether it is possible to serialize a model in 4-bit. Uses most typical params as default.
        See ExtendedSerializationTest class for more params combinations.
        """

        tokenizer = AutoTokenizer.from_pretrained(self.model_name)

        self.quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type=quant_type,
            bnb_4bit_use_double_quant=double_quant,
            bnb_4bit_compute_dtype=torch.bfloat16,
        )

        # for now, we should be able to fetch those in from_pretrained directly
        if self.model_name == "facebook/opt-125m":
            revision = "refs/pr/49"
        else:
            revision = "main"

        model_0 = AutoModelForCausalLM.from_pretrained(
            self.model_name, quantization_config=self.quantization_config, device_map=torch_device, revision=revision
        )

        with tempfile.TemporaryDirectory() as tmpdirname:
            model_0.save_pretrained(tmpdirname)

            config = AutoConfig.from_pretrained(tmpdirname)
            self.assertTrue(hasattr(config, "quantization_config"))

            model_1 = AutoModelForCausalLM.from_pretrained(tmpdirname, device_map=torch_device)

        # checking quantized linear module weight
        linear = get_some_linear_layer(model_1)
        self.assertTrue(linear.weight.__class__ == bnb.nn.Params4bit)
        self.assertTrue(hasattr(linear.weight, "quant_state"))
        self.assertTrue(linear.weight.quant_state.__class__ == bnb.functional.QuantState)

        # checking memory footpring
        self.assertAlmostEqual(model_0.get_memory_footprint() / model_1.get_memory_footprint(), 1, places=2)

        # Matching all parameters and their quant_state items:
        d0 = dict(model_0.named_parameters())
        d1 = dict(model_1.named_parameters())
        self.assertTrue(d0.keys() == d1.keys())

        for k in d0:
            self.assertTrue(d0[k].shape == d1[k].shape)
            self.assertTrue(d0[k].device.type == d1[k].device.type)
            self.assertTrue(d0[k].device == d1[k].device)
            self.assertTrue(d0[k].dtype == d1[k].dtype)
            self.assertTrue(torch.equal(d0[k], d1[k].to(d0[k].device)))

            if isinstance(d0[k], bnb.nn.modules.Params4bit):
                for v0, v1 in zip(
                    d0[k].quant_state.as_dict().values(),
                    d1[k].quant_state.as_dict().values(),
                ):
                    if isinstance(v0, torch.Tensor):
                        # The absmax will not be saved in the quant_state when using NF4 in CPU
                        if v0.numel() != 0:
                            self.assertTrue(torch.equal(v0, v1.to(v0.device)))
                    else:
                        self.assertTrue(v0 == v1)

        # comparing forward() outputs
        encoded_input = tokenizer(self.input_text, return_tensors="pt", return_token_type_ids=False).to(torch_device)
        out_0 = model_0(**encoded_input)
        out_1 = model_1(**encoded_input)
        torch.testing.assert_close(out_0["logits"], out_1["logits"], rtol=0.05, atol=0.05)

        # comparing generate() outputs
        encoded_input = tokenizer(self.input_text, return_tensors="pt", return_token_type_ids=False).to(torch_device)
        output_sequences_0 = model_0.generate(**encoded_input, max_new_tokens=10)
        output_sequences_1 = model_1.generate(**encoded_input, max_new_tokens=10)

        def _decode(token):
            return tokenizer.decode(token, skip_special_tokens=True)

        self.assertEqual(
            [_decode(x) for x in output_sequences_0],
            [_decode(x) for x in output_sequences_1],
        )