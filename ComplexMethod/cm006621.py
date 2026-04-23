def test_build_model_params_structure(self, mock_chatwatsonx, wx_component):
        """Test that model params are structured correctly."""
        wx_component.api_key = "test-api-key"  # pragma: allowlist secret
        wx_component.base_url = "https://us-south.ml.cloud.ibm.com"
        wx_component.project_id = "test-project-id"
        wx_component.space_id = None
        wx_component.model_name = "ibm/granite-3-8b-instruct"
        wx_component.stream = False
        wx_component.max_tokens = 1500
        wx_component.temperature = 0.8
        wx_component.top_p = 0.85
        wx_component.frequency_penalty = 0.6
        wx_component.presence_penalty = 0.4
        wx_component.seed = 123
        wx_component.stop_sequence = "STOP"
        wx_component.logprobs = True
        wx_component.top_logprobs = 10
        wx_component.logit_bias = None

        wx_component.build_model()

        call_kwargs = mock_chatwatsonx.call_args[1]
        params = call_kwargs["params"]

        assert params["max_tokens"] == 1500
        assert params["temperature"] == 0.8
        assert params["top_p"] == 0.85
        assert params["frequency_penalty"] == 0.6
        assert params["presence_penalty"] == 0.4
        assert params["seed"] == 123
        assert params["stop"] == ["STOP"]
        assert params["n"] == 1
        assert params["logprobs"] is True
        assert params["top_logprobs"] == 10
        assert params["time_limit"] == 600000
        assert params["logit_bias"] is None