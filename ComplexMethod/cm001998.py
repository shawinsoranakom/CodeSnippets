def test_sdpa_can_dispatch_composite_models(self):
        """
        Tests if composite models dispatch correctly on SDPA/eager when requested so when loading the model.
        This tests only by looking at layer names, as usually SDPA layers are calles "SDPAAttention".
        In contrast to the above test, this one checks if the "config._attn_implementation" is a dict after the model
        is loaded, because we manually replicate requested attn implementation on each sub-config when loading.
        See https://github.com/huggingface/transformers/pull/32238 for more info

        The test tries to cover most general cases of composite models, VLMs with vision and text configs. Any model
        that has a different set of sub-configs has to overwrite this test.
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

                model_eager = model_class.from_pretrained(tmpdirname, attn_implementation="eager")
                model_eager = model_eager.eval().to(torch_device)

                # Root model determines SDPA support
                attn_impl = "sdpa" if model._supports_sdpa else "eager"

                self.assertTrue(model_sdpa.config._attn_implementation == "sdpa")
                self.assertTrue(model_sdpa.vision_encoder.config._attn_implementation == attn_impl)
                self.assertTrue(model_sdpa.mask_decoder.config._attn_implementation == attn_impl)

                self.assertTrue(model_eager.config._attn_implementation == "eager")
                self.assertTrue(model_eager.vision_encoder.config._attn_implementation == "eager")
                self.assertTrue(model_eager.mask_decoder.config._attn_implementation == "eager")

                # Verify SDPA/eager layer presence
                has_sdpa = False
                for name, submodule in model_sdpa.named_modules():
                    class_name = submodule.__class__.__name__
                    if "SdpaAttention" in class_name or "SdpaSelfAttention" in class_name:
                        has_sdpa = True
                        break

                if not has_sdpa and attn_impl == "sdpa":
                    raise ValueError("The SDPA model should have SDPA attention layers")

                for name, submodule in model_eager.named_modules():
                    class_name = submodule.__class__.__name__
                    if "SdpaAttention" in class_name or "SdpaSelfAttention" in class_name:
                        raise ValueError("The eager model should not have SDPA attention layers")