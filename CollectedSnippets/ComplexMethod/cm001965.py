def test_sdpa_can_dispatch_composite_models(self):
        if not self.supports_sdpa:
            self.skipTest("SDPA is not supported")

        inputs_dict = self.prepare_config_and_inputs()
        encoder_config, decoder_config = inputs_dict["config"], inputs_dict["decoder_config"]
        config = EncoderDecoderConfig.from_encoder_decoder_configs(
            encoder_config=encoder_config, decoder_config=decoder_config
        )
        model = EncoderDecoderModel(config=config)

        with tempfile.TemporaryDirectory() as tmpdirname:
            model.save_pretrained(tmpdirname)
            model_sdpa = EncoderDecoderModel.from_pretrained(tmpdirname)
            model_sdpa = model_sdpa.eval().to(torch_device)

            # see https://github.com/huggingface/transformers/pull/32238
            # Sub-model will dispatch to SDPA if it can (checked below that `SDPA` layers are present)
            encoder_attn = "sdpa" if model.encoder._supports_sdpa else "eager"
            decoder_attn = "sdpa" if model.decoder._supports_sdpa else "eager"
            self.assertTrue(model_sdpa.config._attn_implementation == "sdpa")
            self.assertTrue(model_sdpa.encoder.config._attn_implementation == encoder_attn)
            self.assertTrue(model_sdpa.decoder.config._attn_implementation == decoder_attn)

            # Also test that nothing break if we request SDPA explicitly, when both sub-parts support it.
            # If the model supports sdpa (i.e. all of sub-models supports it) we'll dispatch safely
            # Otherwise we should raise error that SDPA is not supported, as some of the sub-models doesn't support
            if encoder_attn == "sdpa" and decoder_attn == "sdpa":
                model_sdpa_explicit = EncoderDecoderModel.from_pretrained(tmpdirname, attn_implementation="sdpa")
                model_sdpa_explicit = model_sdpa_explicit.eval().to(torch_device)

                self.assertTrue(model_sdpa_explicit.config._attn_implementation == "sdpa")
            else:
                with self.assertRaises(ValueError):
                    model_sdpa_explicit = EncoderDecoderModel.from_pretrained(tmpdirname, attn_implementation="sdpa")

            model_eager = EncoderDecoderModel.from_pretrained(
                tmpdirname,
                attn_implementation="eager",
            )
            model_eager = model_eager.eval().to(torch_device)

            self.assertTrue(model_eager.config._attn_implementation == "eager")
            self.assertTrue(model_eager.encoder.config._attn_implementation == "eager")
            self.assertTrue(model_eager.decoder.config._attn_implementation == "eager")

            for name, submodule in model_eager.named_modules():
                class_name = submodule.__class__.__name__
                if "SdpaAttention" in class_name or "SdpaSelfAttention" in class_name:
                    raise ValueError("The eager model should not have SDPA attention layers")