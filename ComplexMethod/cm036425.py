def test_fp8_reloading(
    default_vllm_config,
    method_cls,
    is_checkpoint_fp8_serialized,
    weight_block_size,
    use_marlin,
    dist_init,
    monkeypatch,
):
    # NOTE(rob): this test fails when using DeepGEMM because the
    # shapes are invalid. Previously the test was passing because
    # we set fp8_backend to None, which sidestepped the issue.
    monkeypatch.setenv("VLLM_USE_DEEP_GEMM", "0")

    if is_checkpoint_fp8_serialized is False:
        pytest.skip("FP8 weight reloading does not support online quantization")

    if method_cls is Fp8MoEMethod and weight_block_size is None:
        pytest.skip(
            "FP8 Tensor weight reloading does not support fusing w13_weight_scale. "
            "If this is your use case, consider using a restore function like #26327"
        )

    # Set model config as model_config.dtype is required in Fp8LinearMethod.
    default_vllm_config.model_config = ModelConfig()
    with torch.device(f"{DEVICE_TYPE}:0"):
        config = Fp8Config(
            is_checkpoint_fp8_serialized=is_checkpoint_fp8_serialized,
            weight_block_size=weight_block_size,
        )

        if method_cls is Fp8LinearMethod:
            layer = torch.nn.Linear(1, 1)
            method = method_cls(config)
            method.create_weights(
                layer=layer,
                input_size_per_partition=1,
                output_partition_sizes=[1],
                input_size=1,
                output_size=1,
                params_dtype=torch.bfloat16,
                weight_loader=default_weight_loader,
            )
            method.use_marlin = use_marlin

        else:
            layer = FusedMoE(
                num_experts=1,
                top_k=1,
                hidden_size=1,
                intermediate_size=1,
            )
            method = method_cls(config, layer)
            method.create_weights(
                layer=layer,
                num_experts=1,
                hidden_size=1,
                intermediate_size_per_partition=1,
                params_dtype=torch.bfloat16,
                weight_loader=default_weight_loader,
            )

    # capture weights format during loading
    original_metadata = [
        (name, param.shape, getattr(param, "weight_loader", default_weight_loader))
        for name, param in layer.named_parameters()
    ]

    # test loading
    for name, shape, _ in original_metadata:
        param = getattr(layer, name)
        weight_loader = getattr(param, "weight_loader", default_weight_loader)
        weight_loader(param, torch.zeros(shape))  # cannot use empty

    method.process_weights_after_loading(layer)

    # test reloading works after loading
    # assuming that no reshaping occurred
    for name, shape, original_weight_loader in original_metadata:
        param = getattr(layer, name)
        weight_loader = getattr(param, "weight_loader", default_weight_loader)
        assert weight_loader is original_weight_loader
        weight_loader(param, torch.zeros(shape))  # cannot use empty

    method.process_weights_after_loading(layer)