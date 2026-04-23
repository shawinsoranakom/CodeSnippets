def test_bge_m3_sparse_plugin_offline(vllm_runner, return_tokens: bool):
    """Test BGE-M3 sparse plugin in offline mode."""
    prompt = {
        "data": {
            "input": model_config["test_input"],
            "return_tokens": return_tokens,
        }
    }

    with vllm_runner(
        model_config["model_name"],
        runner="pooling",
        enforce_eager=True,
        max_num_seqs=32,
        io_processor_plugin=model_config["plugin"],
        hf_overrides=json.loads(model_config["hf_overrides"]),
        default_torch_num_threads=1,
    ) as llm_runner:
        llm = llm_runner.get_llm()
        pooler_output = llm.encode(prompt, pooling_task="plugin")

    outputs = pooler_output[0]

    # Verify output structure
    assert hasattr(outputs, "outputs")
    response = outputs.outputs
    assert hasattr(response, "data")
    assert len(response.data) == 1
    # Verify response data
    for i, output in enumerate(response.data):
        # Each output should have sparse embeddings
        sparse_embedding = output.sparse_embedding
        assert isinstance(sparse_embedding, list)
        _check_sparse_embedding(sparse_embedding, return_tokens)
        dense_embedding = output.dense_embedding
        assert isinstance(dense_embedding, list)
        _check_dense_embedding(dense_embedding)

    # Verify usage
    assert response.usage.prompt_tokens > 0
    assert response.usage.total_tokens == response.usage.prompt_tokens