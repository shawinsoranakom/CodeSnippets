def test_fetch_models_success(self, mock_get, mock_response):
        """Test successful model fetching from API."""
        from lfx.components.ibm.watsonx_embeddings import WatsonxEmbeddingsComponent

        mock_get.return_value = mock_response

        models = WatsonxEmbeddingsComponent.fetch_models("https://us-south.ml.cloud.ibm.com")

        assert len(models) == 4
        assert "sentence-transformers/all-minilm-l12-v2" in models
        assert "ibm/slate-125m-english-rtrvr-v2" in models
        assert "ibm/slate-30m-english-rtrvr-v2" in models
        assert "intfloat/multilingual-e5-large" in models

        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "https://us-south.ml.cloud.ibm.com/ml/v1/foundation_model_specs" in call_args[0]
        assert call_args[1]["params"]["version"] == "2024-09-16"
        assert call_args[1]["params"]["filters"] == "function_embedding,!lifecycle_withdrawn:and"
        assert call_args[1]["timeout"] == 10