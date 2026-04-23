def test_get_video_features_output(self, return_dict: bool | None):
        for model_class in self.all_model_classes:
            if not hasattr(model_class, "get_video_features"):
                continue

            config, inputs_dict = self._video_features_prepare_config_and_inputs()
            if return_dict is not None:
                config.return_dict = return_dict

            model = model_class(config).eval()
            model = model.to(torch_device)

            set_seed(42)
            with torch.no_grad():
                outputs = model.get_video_features(**inputs_dict)

            if return_dict in (True, None):
                self.assertTrue(isinstance(outputs, ModelOutput), "get_video_features() must return a BaseModelOutput")
                self.assertTrue(
                    hasattr(outputs, "last_hidden_state"),
                    "get_video_features() must return a BaseModelOutput with last_hidden_state",
                )
                self.assertTrue(
                    hasattr(outputs, "pooler_output"),
                    "get_video_features() must return a BaseModelOutput with pooler_output",
                )
                self.assertTrue(
                    hasattr(outputs, "hidden_states"),
                    "get_video_features() must return a BaseModelOutput with hidden_states",
                )
                if self.has_attentions:
                    self.assertTrue(
                        hasattr(outputs, "attentions"),
                        "get_video_features() must return a BaseModelOutput with attentions",
                    )

                if getattr(self, "skip_test_video_features_output_shape", False):
                    return

                last_hidden_state_shape = outputs.last_hidden_state.shape
                if "pixel_values_videos" in inputs_dict:
                    batch_size = inputs_dict["pixel_values_videos"].shape[0]
                elif "pixel_values" in inputs_dict:
                    batch_size = inputs_dict["pixel_values"].shape[0]
                self.assertEqual(
                    last_hidden_state_shape[0],
                    batch_size,
                    f"batch_size mismatch, full shape: {last_hidden_state_shape}",
                )
                video_config = config
                if hasattr(config, "video_config"):
                    video_config = config.video_config
                elif hasattr(config, "vision_config"):
                    video_config = config.vision_config
                if hasattr(video_config, "out_hidden_size"):
                    hidden_size = video_config.out_hidden_size
                else:
                    hidden_size = video_config.hidden_size
                self.assertEqual(
                    last_hidden_state_shape[-1],
                    hidden_size,
                    f"hidden_size mismatch, full shape: {last_hidden_state_shape}",
                )

            else:
                self.assertIsInstance(outputs, tuple, "get_video_features() must return a tuple if return_dict=False")