def test_bge_m3_sparse_plugin_offline_multiple_inputs(vllm_runner):
    """Test BGE-M3 sparse plugin with multiple inputs in offline mode."""
    prompts = {
        "data": {
            "input": [
                "What is the capital of France?",
                "What is the capital of Germany?",
                "What is the capital of Spain?",
            ],
            "return_tokens": True,
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
        pooler_output = llm.encode(prompts, pooling_task="plugin")

    outputs = pooler_output[0]

    # Verify output structure
    assert hasattr(outputs, "outputs")
    response = outputs.outputs
    assert hasattr(response, "data")
    assert len(response.data) == 3
    for i, output in enumerate(response.data):
        # Each output should have sparse embeddings
        sparse_embedding = output.sparse_embedding
        assert isinstance(sparse_embedding, list)
        dense_embedding = output.dense_embedding
        assert isinstance(dense_embedding, list)
        _check_dense_embedding(dense_embedding, i)

    # Verify usage
    assert response.usage.prompt_tokens > 0
    assert response.usage.total_tokens == response.usage.prompt_tokens