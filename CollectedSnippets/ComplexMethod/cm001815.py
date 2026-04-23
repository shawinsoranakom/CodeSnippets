def test_zero3_load_registered_buffers(self):
        """Test that registered buffers are loaded with correct values under ZeRO-3 from_pretrained."""
        from transformers.models.gemma4.configuration_gemma4 import (
            Gemma4AudioConfig,
            Gemma4Config,
            Gemma4TextConfig,
            Gemma4VisionConfig,
        )
        from transformers.models.gemma4.modeling_gemma4 import Gemma4ForConditionalGeneration

        text_config = Gemma4TextConfig(
            hidden_size=128,
            num_hidden_layers=2,
            num_attention_heads=2,
            intermediate_size=256,
            vocab_size=32000,
            num_key_value_heads=2,
            pad_token_id=0,
        )
        vision_config = Gemma4VisionConfig(
            hidden_size=64, num_hidden_layers=2, num_attention_heads=2, intermediate_size=128
        )
        audio_config = Gemma4AudioConfig()
        config = Gemma4Config(text_config=text_config, vision_config=vision_config, audio_config=audio_config)

        # Save without ZeRO-3, with non-default buffer values
        save_path = self.get_auto_remove_tmp_dir()
        model = Gemma4ForConditionalGeneration(config)
        for name, buf in model.named_buffers():
            if "input_max" in name:
                buf.fill_(42.0)
            elif "output_min" in name:
                buf.fill_(-42.0)
            elif "layer_scalar" in name:
                buf.fill_(0.5)
        model.save_pretrained(save_path)
        del model

        # Load with ZeRO-3
        ds_config = self._get_zero3_ds_config(bf16={"enabled": True})
        dschf = HfDeepSpeedConfig(ds_config)
        self.assertTrue(dschf.is_zero3())
        with mockenv_context(**self.dist_env_1_gpu):
            model2 = Gemma4ForConditionalGeneration.from_pretrained(save_path, torch_dtype=torch.bfloat16)

        # Verify buffer VALUES were loaded from checkpoint, not re-initialized
        for name, buf in model2.named_buffers():
            if "input_max" in name:
                self.assertEqual(buf.item(), 42.0, f"{name} was not loaded from checkpoint")
            elif "output_min" in name:
                self.assertEqual(buf.item(), -42.0, f"{name} was not loaded from checkpoint")
            elif "layer_scalar" in name:
                self.assertEqual(buf.item(), 0.5, f"{name} was not loaded from checkpoint")