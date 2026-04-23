def _video_features_prepare_config_and_inputs(self):
        """
        Helper method to extract only video-related inputs from the full set of inputs, for testing `get_video_features`.

        Specifically, it tests both the model_tester and its video_model_tester (if any),
        and filters for keys related to videos. It also handles key renaming for video inputs
        if there is no dedicated video_model_tester.
        """
        config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
        if hasattr(self.model_tester, "video_model_tester"):
            _, inputs_dict = self.model_tester.video_model_tester.prepare_config_and_inputs_for_common()
        else:
            key_mappings = {
                "pixel_values": "pixel_values_videos",
                "image_grid_thw": "video_grid_thw",
                "image_merge_sizes": "video_merge_sizes",
            }

            for src_key, dst_key in key_mappings.items():
                if src_key in inputs_dict and dst_key not in inputs_dict:
                    inputs_dict[dst_key] = inputs_dict.pop(src_key)

            allowed_non_video_keys = {"vision_feature_layer", "vision_feature_select_strategy", "cu_seqlens"}
            inputs_dict = {
                key: value for key, value in inputs_dict.items() if "video" in key or key in allowed_non_video_keys
            }
        return config, inputs_dict