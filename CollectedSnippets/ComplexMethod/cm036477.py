def test_roberta_model_loading_with_params(vllm_runner, monkeypatch):
    """
    Test parameter weight loading with tp>1.
    """
    # to use apply_model
    monkeypatch.setenv("VLLM_ALLOW_INSECURE_SERIALIZATION", "1")
    with vllm_runner(
        model_name=MODEL_NAME_ROBERTA,
        revision=REVISION_ROBERTA,
        dtype="float16",
        max_model_len=MAX_MODEL_LEN,
    ) as vllm_model:
        output = vllm_model.embed(
            "Write a short story about a robot that dreams for the first time.\n"
        )

        model_config = vllm_model.llm.llm_engine.model_config
        model_tokenizer = vllm_model.llm.llm_engine.tokenizer

        # asserts on the bert model config file
        assert model_config.encoder_config["max_seq_length"] == 512
        assert not model_config.encoder_config["do_lower_case"]

        # asserts on the pooling config files
        assert model_config.pooler_config.seq_pooling_type == "MEAN"
        assert model_config.pooler_config.tok_pooling_type == "ALL"
        assert model_config.pooler_config.use_activation

        # asserts on the tokenizer loaded
        assert model_config.tokenizer == "intfloat/multilingual-e5-base"
        assert model_tokenizer.model_max_length == 512

        def check_model(model):
            assert isinstance(model, RobertaEmbeddingModel)
            assert isinstance(pooler := model.pooler, DispatchPooler)
            assert isinstance(pooler.poolers_by_task["embed"].pooling, MeanPool)

        vllm_model.apply_model(check_model)

        assert output