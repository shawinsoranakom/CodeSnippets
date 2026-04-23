def test_get_audio_features_output(self, return_dict: bool | None):
        for model_class in self.all_model_classes:
            if not hasattr(model_class, "get_audio_features"):
                continue

            config, inputs_dict = self._audio_features_prepare_config_and_inputs()
            if return_dict is not None:
                config.return_dict = return_dict

            model = model_class(config).eval()
            model = model.to(torch_device)

            set_seed(42)
            with torch.no_grad():
                outputs = model.get_audio_features(**inputs_dict)

            if return_dict in (True, None):
                self.assertTrue(
                    isinstance(outputs, ModelOutput), "get_audio_features() must return a BaseModelOutputWithPooling"
                )
                self.assertTrue(
                    hasattr(outputs, "last_hidden_state"),
                    "get_audio_features() must return a BaseModelOutputWithPooling with last_hidden_state",
                )
                self.assertTrue(
                    hasattr(outputs, "pooler_output"),
                    "get_audio_features() must return a BaseModelOutputWithPooling with pooler_output",
                )
                self.assertTrue(
                    hasattr(outputs, "hidden_states"),
                    "get_audio_features() must return a BaseModelOutputWithPooling with hidden_states",
                )
                if self.has_attentions:
                    self.assertTrue(
                        hasattr(outputs, "attentions"),
                        "get_audio_features() must return a BaseModelOutputWithPooling with attentions",
                    )

                if getattr(self, "skip_test_audio_features_output_shape", False):
                    return

                last_hidden_state_shape = outputs.last_hidden_state.shape

                if "input_features" in inputs_dict:
                    batch_size = inputs_dict["input_features"].shape[0]
                else:
                    batch_size = inputs_dict["input_values"].shape[0]
                self.assertEqual(
                    last_hidden_state_shape[0],
                    batch_size,
                    f"batch_size mismatch, full shape: {last_hidden_state_shape}",
                )

                audio_config = config.audio_config if hasattr(config, "audio_config") else config
                if hasattr(audio_config, "projection_dim"):
                    hidden_size = audio_config.projection_dim
                elif hasattr(audio_config, "hidden_size"):
                    hidden_size = audio_config.hidden_size
                elif hasattr(audio_config, "encoder_config"):
                    hidden_size = audio_config.encoder_config.hidden_dim
                elif hasattr(audio_config, "encoder_ffn_dim"):
                    hidden_size = audio_config.encoder_ffn_dim
                self.assertEqual(
                    last_hidden_state_shape[-1],
                    hidden_size,
                    f"hidden_size mismatch, full shape: {last_hidden_state_shape}",
                )

            else:
                self.assertIsInstance(outputs, tuple, "get_audio_features() must return a tuple if return_dict=False")