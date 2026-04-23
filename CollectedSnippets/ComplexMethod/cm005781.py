def test_get_embeddings_watsonx_truncate_and_input_text(mock_get_vars, mock_get_class, mock_get_api_key):
    """truncate_input_tokens and input_text should be passed as WatsonX params dict."""
    mock_get_api_key.return_value = "ibm-key"
    mock_get_vars.return_value = {}
    mock_embedding_class = MagicMock()
    mock_get_class.return_value = mock_embedding_class

    watsonx_model = {
        "name": "ibm/slate-125m-english-rtrvr",
        "provider": "IBM WatsonX",
        "metadata": {
            "embedding_class": "WatsonxEmbeddings",
            "param_mapping": {
                "model_id": "model_id",
                "api_key": "apikey",  # pragma: allowlist secret
                "url": "url",
                "project_id": "project_id",
            },
        },
    }

    get_embeddings(
        [watsonx_model],
        api_key="ibm-key",  # pragma: allowlist secret
        watsonx_url="https://us-south.ml.cloud.ibm.com",
        watsonx_project_id="proj-123",
        watsonx_truncate_input_tokens=200,
        watsonx_input_text=True,
    )

    kwargs = mock_embedding_class.call_args.kwargs
    assert "params" in kwargs
    params = kwargs["params"]
    # Check truncate_input_tokens is present (key may be enum or string depending on ibm_watsonx_ai availability)
    truncate_values = [v for v in params.values() if v == 200]
    assert truncate_values, "Expected truncate_input_tokens=200 in params"
    # Check return_options contains input_text
    return_opts = [v for v in params.values() if isinstance(v, dict) and "input_text" in v]
    assert return_opts, "Expected return_options with input_text in params"
    assert return_opts[0]["input_text"] is True