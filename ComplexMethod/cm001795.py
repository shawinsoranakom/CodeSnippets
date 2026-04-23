def test_get_image_features_output(self, return_dict: bool | None):
        for model_class in self.all_model_classes:
            if not hasattr(model_class, "get_image_features"):
                continue

            config, inputs_dict = self._image_features_prepare_config_and_inputs()
            if return_dict is not None:
                config.return_dict = return_dict

            model = model_class(config).eval()
            model = model.to(torch_device)

            set_seed(42)
            with torch.no_grad():
                outputs = model.get_image_features(**inputs_dict)

            if return_dict in (True, None):
                self.assertTrue(isinstance(outputs, ModelOutput), "get_image_features() must return a BaseModelOutput")
                self.assertTrue(
                    hasattr(outputs, "last_hidden_state"),
                    "get_image_features() must return a BaseModelOutput with last_hidden_state",
                )
                self.assertTrue(
                    hasattr(outputs, "pooler_output"),
                    "get_image_features() must return a BaseModelOutput with pooler_output",
                )
                self.assertTrue(
                    hasattr(outputs, "hidden_states"),
                    "get_image_features() must return a BaseModelOutput with hidden_states",
                )
                if self.has_attentions:
                    self.assertTrue(
                        hasattr(outputs, "attentions"),
                        "get_image_features() must return a BaseModelOutput with attentions",
                    )

                if getattr(self, "skip_test_image_features_output_shape", False):
                    return

                last_hidden_state_shape = outputs.last_hidden_state.shape
                batch_size = (
                    inputs_dict["pixel_values"].shape[0]
                    if "pixel_values" in inputs_dict
                    else inputs_dict["pixel_values_images"].shape[0]
                )
                self.assertEqual(
                    last_hidden_state_shape[0],
                    batch_size,
                    f"batch_size mismatch, full shape: {last_hidden_state_shape}",
                )

                vision_config = config.vision_config if hasattr(config, "vision_config") else config
                vision_config = (
                    vision_config.backbone_config if hasattr(vision_config, "backbone_config") else vision_config
                )
                vision_config = vision_config.vq_config if hasattr(vision_config, "vq_config") else vision_config
                vision_config = vision_config.model_args if hasattr(vision_config, "model_args") else vision_config
                attribute_candidates = [
                    "embed_dim_per_stage",
                    "embed_dim",
                    "embed_dims",
                    "out_hidden_size",
                    "hidden_size",
                    "hidden_dim",
                ]
                hidden_size = None
                for attr in attribute_candidates:
                    if hasattr(vision_config, attr):
                        hidden_size = getattr(vision_config, attr)
                        break
                    elif isinstance(vision_config, dict) and attr in vision_config:
                        hidden_size = vision_config[attr]
                        break
                else:
                    raise ValueError("Cannot find the hidden size attribute in vision_config")
                if isinstance(hidden_size, (list, tuple)):
                    hidden_size = hidden_size[-1]
                self.assertEqual(
                    last_hidden_state_shape[-1],
                    hidden_size,
                    f"hidden_size mismatch, full shape: {last_hidden_state_shape}",
                )

            else:
                self.assertIsInstance(outputs, tuple, "get_image_features() must return a tuple if return_dict=False")