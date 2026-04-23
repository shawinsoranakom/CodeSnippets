async def test_bge_m3_sparse_plugin_online(
    server: RemoteOpenAIServer, return_tokens: bool
):
    """Test BGE-M3 sparse plugin in online mode via API."""
    request_payload = {
        "model": model_config["model_name"],
        "task": "plugin",
        "data": {"input": model_config["test_input"], "return_tokens": return_tokens},
    }

    ret = requests.post(
        server.url_for("pooling"),
        json=request_payload,
    )

    response = ret.json()

    # Verify the request response is in the correct format
    assert (parsed_response := IOProcessorResponse(**response).data)

    # Verify the output is formatted as expected for this plugin
    assert _get_attr_or_val(parsed_response, "data")
    assert len(_get_attr_or_val(parsed_response, "data")) > 0

    data_entry = _get_attr_or_val(parsed_response, "data")[0]
    assert _get_attr_or_val(data_entry, "object") == "dense&sparse"
    assert _get_attr_or_val(data_entry, "sparse_embedding")

    # Verify sparse embedding format
    sparse_embedding = _get_attr_or_val(data_entry, "sparse_embedding")
    assert isinstance(sparse_embedding, list)
    _check_sparse_embedding(sparse_embedding, return_tokens)

    # Verify dense embedding format
    dense_embedding = _get_attr_or_val(data_entry, "dense_embedding")
    assert isinstance(dense_embedding, list)
    _check_dense_embedding(dense_embedding)

    # Verify usage information
    usage = _get_attr_or_val(parsed_response, "usage")
    assert usage, f"usage not found for {parsed_response}"
    assert _get_attr_or_val(usage, "prompt_tokens") > 0
    assert _get_attr_or_val(usage, "total_tokens") == _get_attr_or_val(
        usage, "prompt_tokens"
    )