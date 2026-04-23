def test_attention_config():
    from vllm.v1.attention.backends.registry import AttentionBackendEnum

    parser = EngineArgs.add_cli_args(FlexibleArgumentParser())

    # default value
    args = parser.parse_args([])
    assert args is not None
    engine_args = EngineArgs.from_cli_args(args)
    assert engine_args.attention_config == AttentionConfig()

    # set backend via dot notation
    args = parser.parse_args(["--attention-config.backend", "FLASH_ATTN"])
    assert args is not None
    engine_args = EngineArgs.from_cli_args(args)
    assert engine_args.attention_config.backend is not None
    assert engine_args.attention_config.backend.name == "FLASH_ATTN"

    # set backend via --attention-backend shorthand
    args = parser.parse_args(["--attention-backend", "FLASHINFER"])
    assert args is not None
    engine_args = EngineArgs.from_cli_args(args)
    assert engine_args.attention_backend is not None
    assert engine_args.attention_backend == "FLASHINFER"

    # set all fields via dot notation
    args = parser.parse_args(
        [
            "--attention-config.backend",
            "FLASH_ATTN",
            "--attention-config.flash_attn_version",
            "3",
            "--attention-config.use_prefill_decode_attention",
            "true",
            "--attention-config.flash_attn_max_num_splits_for_cuda_graph",
            "16",
            "--attention-config.use_cudnn_prefill",
            "true",
            "--attention-config.use_trtllm_ragged_deepseek_prefill",
            "true",
            "--attention-config.use_trtllm_attention",
            "true",
            "--attention-config.disable_flashinfer_prefill",
            "true",
            "--attention-config.disable_flashinfer_q_quantization",
            "true",
        ]
    )
    assert args is not None
    engine_args = EngineArgs.from_cli_args(args)
    assert engine_args.attention_config.backend is not None
    assert engine_args.attention_config.backend.name == "FLASH_ATTN"
    assert engine_args.attention_config.flash_attn_version == 3
    assert engine_args.attention_config.use_prefill_decode_attention is True
    assert engine_args.attention_config.flash_attn_max_num_splits_for_cuda_graph == 16
    assert engine_args.attention_config.use_cudnn_prefill is True
    assert engine_args.attention_config.use_trtllm_ragged_deepseek_prefill is True
    assert engine_args.attention_config.use_trtllm_attention is True
    assert engine_args.attention_config.disable_flashinfer_prefill is True
    assert engine_args.attention_config.disable_flashinfer_q_quantization is True

    # set to string form of a dict with all fields
    args = parser.parse_args(
        [
            "--attention-config="
            '{"backend": "FLASHINFER", "flash_attn_version": 2, '
            '"use_prefill_decode_attention": false, '
            '"flash_attn_max_num_splits_for_cuda_graph": 8, '
            '"use_cudnn_prefill": false, '
            '"use_trtllm_ragged_deepseek_prefill": false, '
            '"use_trtllm_attention": false, '
            '"disable_flashinfer_prefill": false, '
            '"disable_flashinfer_q_quantization": false}',
        ]
    )
    assert args is not None
    engine_args = EngineArgs.from_cli_args(args)
    assert engine_args.attention_config.backend is not None
    assert engine_args.attention_config.backend.name == "FLASHINFER"
    assert engine_args.attention_config.flash_attn_version == 2
    assert engine_args.attention_config.use_prefill_decode_attention is False
    assert engine_args.attention_config.flash_attn_max_num_splits_for_cuda_graph == 8
    assert engine_args.attention_config.use_cudnn_prefill is False
    assert engine_args.attention_config.use_trtllm_ragged_deepseek_prefill is False
    assert engine_args.attention_config.use_trtllm_attention is False
    assert engine_args.attention_config.disable_flashinfer_prefill is False
    assert engine_args.attention_config.disable_flashinfer_q_quantization is False

    # test --attention-backend flows into VllmConfig.attention_config
    args = parser.parse_args(
        [
            "--model",
            "facebook/opt-125m",
            "--attention-backend",
            "FLASH_ATTN",
        ]
    )
    assert args is not None
    engine_args = EngineArgs.from_cli_args(args)
    vllm_config = engine_args.create_engine_config()
    assert vllm_config.attention_config.backend == AttentionBackendEnum.FLASH_ATTN

    # test --attention-config.backend flows into VllmConfig.attention_config
    args = parser.parse_args(
        [
            "--model",
            "facebook/opt-125m",
            "--attention-config.backend",
            "FLASHINFER",
        ]
    )
    assert args is not None
    engine_args = EngineArgs.from_cli_args(args)
    vllm_config = engine_args.create_engine_config()
    assert vllm_config.attention_config.backend == AttentionBackendEnum.FLASHINFER

    # test --attention-backend and --attention-config.backend are mutually exclusive
    args = parser.parse_args(
        [
            "--model",
            "facebook/opt-125m",
            "--attention-backend",
            "FLASH_ATTN",
            "--attention-config.backend",
            "FLASHINFER",
        ]
    )
    assert args is not None
    engine_args = EngineArgs.from_cli_args(args)
    with pytest.raises(ValueError, match="mutually exclusive"):
        engine_args.create_engine_config()