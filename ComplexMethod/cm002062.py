def test_sdpa_can_dispatch_composite_models(self):
        """
        Tests if composite models dispatch correctly on SDPA/eager when requested.
        SAM3 has multiple sub-models: vision_encoder, text_encoder, geometry_encoder,
        detr_encoder, detr_decoder, mask_decoder.
        """
        if not self.has_attentions:
            self.skipTest(reason="Model architecture does not support attentions")

        if not self._is_composite:
            self.skipTest(f"{self.all_model_classes[0].__name__} does not support SDPA")

        for model_class in self.all_model_classes:
            config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
            model = model_class(config)

            with tempfile.TemporaryDirectory() as tmpdirname:
                model.save_pretrained(tmpdirname)
                model_sdpa = model_class.from_pretrained(tmpdirname, attn_implementation="sdpa")
                model_sdpa = model_sdpa.eval().to(torch_device)

                # Get all sub-models that support attention
                vision_encoder_sdpa = getattr(model_sdpa, "vision_encoder")
                text_encoder_sdpa = getattr(model_sdpa, "text_encoder", None)
                detr_encoder_sdpa = getattr(model_sdpa, "detr_encoder", None)
                detr_decoder_sdpa = getattr(model_sdpa, "detr_decoder", None)
                mask_decoder_sdpa = getattr(model_sdpa, "mask_decoder", None)

                # Check that sub-models dispatch to SDPA if they support it
                self.assertTrue(vision_encoder_sdpa.config._attn_implementation == "sdpa")
                if text_encoder_sdpa is not None and hasattr(text_encoder_sdpa, "_supports_sdpa"):
                    # Sam3LiteTextTextModel supports SDPA
                    self.assertTrue(text_encoder_sdpa.config._attn_implementation == "sdpa")
                if detr_encoder_sdpa is not None:
                    self.assertTrue(detr_encoder_sdpa.config._attn_implementation == "sdpa")
                if detr_decoder_sdpa is not None:
                    self.assertTrue(detr_decoder_sdpa.config._attn_implementation == "sdpa")
                if mask_decoder_sdpa is not None:
                    self.assertTrue(mask_decoder_sdpa.config._attn_implementation == "sdpa")

                # Now test with eager
                model_eager = model_class.from_pretrained(tmpdirname, attn_implementation="eager")
                model_eager = model_eager.eval().to(torch_device)

                self.assertTrue(getattr(model_eager, "vision_encoder").config._attn_implementation == "eager")
                if hasattr(model_eager, "text_encoder") and hasattr(model_eager.text_encoder, "config"):
                    self.assertTrue(model_eager.text_encoder.config._attn_implementation == "eager")
                if hasattr(model_eager, "detr_encoder"):
                    self.assertTrue(model_eager.detr_encoder.config._attn_implementation == "eager")
                if hasattr(model_eager, "detr_decoder"):
                    self.assertTrue(model_eager.detr_decoder.config._attn_implementation == "eager")
                if hasattr(model_eager, "mask_decoder"):
                    self.assertTrue(model_eager.mask_decoder.config._attn_implementation == "eager")

                # Verify no SDPA layers in eager model
                for name, submodule in model_eager.named_modules():
                    class_name = submodule.__class__.__name__
                    if (
                        class_name.endswith("Attention")
                        and getattr(submodule, "config", None)
                        and submodule.config._attn_implementation == "sdpa"
                    ):
                        raise ValueError("The eager model should not have SDPA attention layers")