def _audio_features_prepare_config_and_inputs(self):
        """
        Helper method to extract only audio-related inputs from the full set of inputs, for testing `get_audio_features`.

        Specifically, it tests both the model_tester and its audio_model_tester (if any),
        and filters for keys related to audio.
        """
        config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
        if hasattr(self.model_tester, "audio_model_tester"):
            _, inputs_dict = self.model_tester.audio_model_tester.prepare_config_and_inputs_for_common()
        else:
            inputs_dict = {
                key: value
                for key, value in inputs_dict.items()
                if "audio" in key
                or "input_values" in key
                or "input_features" in key
                or key in ["padding_mask", "is_longer", "feature_attention_mask"]
                or (config.model_type == "musicflamingo" and key == "input_ids")
            }
        return config, inputs_dict