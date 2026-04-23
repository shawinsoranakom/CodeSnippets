def test_splitting_ops_dynamic():
    # Default config
    config = VllmConfig()
    # Default V1 config leaves cudagraph mode unset; splitting ops are only
    # populated when the engine decides to use piecewise compilation.
    assert config.compilation_config.cudagraph_mode == CUDAGraphMode.FULL_AND_PIECEWISE
    assert config.compilation_config.splitting_ops_contain_attention()

    # When use_inductor_graph_partition=True
    config = VllmConfig(
        compilation_config=CompilationConfig(
            mode=CompilationMode.VLLM_COMPILE,
            use_inductor_graph_partition=True,
            splitting_ops=["vllm::unified_attention_with_output"],
        )
    )
    # with inductor partition we use splitting_ops directly for
    # partition rules
    assert config.compilation_config.splitting_ops == [
        "vllm::unified_attention_with_output"
    ]

    # When attn_fusion pass enabled.
    config = VllmConfig(
        compilation_config=CompilationConfig(
            mode=CompilationMode.VLLM_COMPILE,
            pass_config=PassConfig(fuse_attn_quant=True, eliminate_noops=True),
            custom_ops=["+quant_fp8"],
            cudagraph_mode=CUDAGraphMode.PIECEWISE,
        )
    )
    assert config.compilation_config.splitting_ops == []
    # cudagraph mode also fall back to FULL
    assert config.compilation_config.cudagraph_mode == CUDAGraphMode.FULL

    # splitting_ops can not contain attention ops when attn_fusion
    # pass enabled.
    with pytest.raises(ValidationError):
        config = VllmConfig(
            compilation_config=CompilationConfig(
                mode=CompilationMode.VLLM_COMPILE,
                pass_config=PassConfig(fuse_attn_quant=True, eliminate_noops=True),
                custom_ops=["+quant_fp8"],
                cudagraph_mode=CUDAGraphMode.PIECEWISE,
                # work around for accessing all attntion ops
                splitting_ops=CompilationConfig()._attention_ops,
            )
        )

    # When both use_inductor_graph_partition and attn_fusion pass enabled.
    config = VllmConfig(
        compilation_config=CompilationConfig(
            mode=CompilationMode.VLLM_COMPILE,
            use_inductor_graph_partition=True,
            pass_config=PassConfig(fuse_attn_quant=True, eliminate_noops=True),
            custom_ops=["+quant_fp8"],
            cudagraph_mode=CUDAGraphMode.PIECEWISE,
        )
    )
    # With inductor graph partition, attn_fusion and splitting_ops
    # work together. Default splitting_ops include attention ops.
    assert config.compilation_config.splitting_ops_contain_attention()
    # fuse_attn_quant is directly supported under
    # use_inductor_graph_partition=True, and cudagraph_mode
    # is unchanged.
    assert config.compilation_config.cudagraph_mode == CUDAGraphMode.PIECEWISE