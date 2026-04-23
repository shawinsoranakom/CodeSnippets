def test_model_specification(
    parser_with_config, cli_config_file, cli_config_file_with_model
):
    # Test model in CLI takes precedence over config
    args = parser_with_config.parse_args(
        ["serve", "cli-model", "--config", cli_config_file_with_model]
    )
    assert args.model_tag == "cli-model"
    assert args.served_model_name == "mymodel"

    # Test model from config file works
    args = parser_with_config.parse_args(
        [
            "serve",
            "--config",
            cli_config_file_with_model,
        ]
    )
    assert args.model == "config-model"
    assert args.served_model_name == "mymodel"

    # Test no model specified anywhere raises error
    with pytest.raises(ValueError, match="No model specified!"):
        parser_with_config.parse_args(["serve", "--config", cli_config_file])

    # Test using --model option raises error
    # with pytest.raises(
    #         ValueError,
    #         match=
    #     ("With `vllm serve`, you should provide the model as a positional "
    #      "argument or in a config file instead of via the `--model` option."),
    # ):
    #     parser_with_config.parse_args(['serve', '--model', 'my-model'])

    # Test using --model option back-compatibility
    # (when back-compatibility ends, the above test should be uncommented
    # and the below test should be removed)
    args = parser_with_config.parse_args(
        [
            "serve",
            "--tensor-parallel-size",
            "2",
            "--model",
            "my-model",
            "--trust-remote-code",
            "--port",
            "8001",
        ]
    )
    assert args.model is None
    assert args.tensor_parallel_size == 2
    assert args.trust_remote_code is True
    assert args.port == 8001

    args = parser_with_config.parse_args(
        [
            "serve",
            "--tensor-parallel-size=2",
            "--model=my-model",
            "--trust-remote-code",
            "--port=8001",
        ]
    )
    assert args.model is None
    assert args.tensor_parallel_size == 2
    assert args.trust_remote_code is True
    assert args.port == 8001

    # Test other config values are preserved
    args = parser_with_config.parse_args(
        [
            "serve",
            "cli-model",
            "--config",
            cli_config_file_with_model,
        ]
    )
    assert args.tensor_parallel_size == 2
    assert args.trust_remote_code is True
    assert args.port == 12312