def _audio_features_get_expected_num_attentions(self, model_tester=None):
        if model_tester is None:
            model_tester = self.model_tester

        if hasattr(model_tester, "audio_model_tester"):
            return self._audio_features_get_expected_num_attentions(model_tester.audio_model_tester)
        elif (
            hasattr(model_tester, "audio_config")
            and isinstance(model_tester.audio_config, dict)
            and "num_hidden_layers" in model_tester.audio_config
        ):
            return model_tester.audio_config["num_hidden_layers"]

        if hasattr(model_tester, "expected_num_hidden_layers"):
            return model_tester.expected_num_hidden_layers - 1
        elif hasattr(model_tester, "num_hidden_layers"):
            return model_tester.num_hidden_layers
        raise ValueError("Cannot determine the expected number of layers for audio features")