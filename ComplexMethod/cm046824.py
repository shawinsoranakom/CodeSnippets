def _test_linear_is_fake_quantized(linear: torch.nn.Linear, qat_scheme: str):
    """
    Verify that the given linear contains fake quantizers according to the `qat_scheme`.
    """
    weight_only = False
    if qat_scheme == "fp8-int4":
        act_fq_class = Float8FakeQuantizer
        weight_fq_class = Int4WeightFakeQuantizer
        min_in_features = 128
    elif qat_scheme == "fp8-fp8":
        act_fq_class = Float8FakeQuantizer
        weight_fq_class = Float8FakeQuantizer
        min_in_features = -1
    elif qat_scheme == "int8":
        act_fq_class = None
        weight_fq_class = IntxFakeQuantizer
        min_in_features = 128
        weight_only = True
    elif qat_scheme == "cactus":
        act_fq_class = None
        weight_fq_class = IntxFakeQuantizer
        min_in_features = 32
        weight_only = True
    else:
        raise ValueError(f"Unknown qat_scheme: {qat_scheme}")

    # Check base layer activations and weights
    base_layer = getattr(linear, "base_layer", linear)
    if base_layer.in_features >= min_in_features:
        assert isinstance(base_layer, FakeQuantizedLinear)
        if not weight_only:
            assert isinstance(base_layer.activation_fake_quantizer, act_fq_class)
        assert isinstance(base_layer.weight_fake_quantizer, weight_fq_class)

    # Check lora A and B (only for full_finetuning=False)
    if hasattr(linear, "lora_A") and hasattr(linear, "lora_B"):
        lora_A = linear.lora_A.default
        lora_B = linear.lora_B.default
        if lora_A.in_features >= min_in_features:
            assert isinstance(lora_A, FakeQuantizedLinear)
            if not weight_only:
                assert isinstance(lora_A.activation_fake_quantizer, act_fq_class)
            assert isinstance(lora_A.weight_fake_quantizer, weight_fq_class)
        if lora_B.in_features >= min_in_features:
            assert isinstance(lora_B, FakeQuantizedLinear)
            if not weight_only:
                assert isinstance(lora_B.activation_fake_quantizer, act_fq_class)
            assert isinstance(lora_B.weight_fake_quantizer, weight_fq_class)