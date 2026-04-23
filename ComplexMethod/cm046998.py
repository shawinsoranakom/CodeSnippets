def _prepare_model_for_qat(
    model: torch.nn.Module, qat_scheme: Union[str, TorchAOConfig]
) -> torch.nn.Module:
    """
    Transform a model for Quantization-Aware Training (QAT) during fine-tuning.

    On a high level, this means fake quantizing the base (frozen) model during training.
    Fake quantization refers to simulating quantization numerics in high precision (e.g. bf16).
    This helps mitigate quantization degradations when the model is quantized after training.

    QAT can be optionally combined with LoRA fine-tuning to for additional throughput improvement.
    For more details: https://dev-discuss.pytorch.org/t/speeding-up-qat-by-1-89x-with-lora/2700
    """
    try:
        from torchao.quantization import PerRow, quantize_
        from torchao.quantization.granularity import PerGroup, PerAxis
        from torchao.quantization.qat import QATConfig
    except ImportError:
        raise ImportError(TORCHAO_MSG)

    # Gemma3 models have issues with int8 embedding quantization due to their
    # large vocabulary size (262144). Auto-switch to int4 weight-only instead.
    if qat_scheme == "int8-int4":
        model_types = get_transformers_model_type(model.config)
        is_gemma3 = any("gemma3" in mt or "gemma_3" in mt for mt in model_types)
        if is_gemma3:
            print(
                "Unsloth: Gemma3 has a large vocabulary causing int8 embedding issues. "
                "Switching to int4 weight-only QAT for training stability."
            )
            qat_scheme = "int4"

    if not isinstance(qat_scheme, TorchAOConfig):
        torchao_config: Optional[TorchAOConfig] = None
        if qat_scheme == "fp8-int4":
            try:
                from torchao.quantization import Float8DynamicActivationInt4WeightConfig
            except ImportError:
                raise ImportError(TORCHAO_MSG)
            group_size = 128
            base_config = Float8DynamicActivationInt4WeightConfig()
            filter_fn = (
                lambda m, _: isinstance(m, torch.nn.Linear)
                and m.in_features >= group_size
            )
            torchao_config = TorchAOConfig(
                qat_scheme = qat_scheme,
                base_config_and_filter_fns = [(base_config, filter_fn)],
            )
        elif qat_scheme == "fp8-fp8":
            try:
                from torchao.quantization import (
                    Float8DynamicActivationFloat8WeightConfig,
                )
            except ImportError:
                raise ImportError(TORCHAO_MSG)
            base_config = Float8DynamicActivationFloat8WeightConfig(
                granularity = PerRow()
            )
            torchao_config = TorchAOConfig(
                qat_scheme = qat_scheme, base_config_and_filter_fns = [(base_config, None)]
            )
        elif qat_scheme == "int8-int4":
            try:
                from torchao.quantization import (
                    Int8DynamicActivationIntxWeightConfig,
                    IntxWeightOnlyConfig,
                )
            except ImportError:
                raise ImportError(TORCHAO_MSG)
            torchao_config = TorchAOConfig(
                qat_scheme = qat_scheme,
                base_config_and_filter_fns = [
                    (
                        IntxWeightOnlyConfig(
                            weight_dtype = torch.int8, granularity = PerAxis(0)
                        ),
                        lambda m, fqn: isinstance(m, torch.nn.Embedding),
                    ),
                    (
                        Int8DynamicActivationIntxWeightConfig(
                            weight_dtype = torch.int4, weight_granularity = PerGroup(32)
                        ),
                        None,
                    ),
                ],
                prequantization_transform = _untie_input_output_embeddings,
            )
        elif qat_scheme == "int4":
            try:
                from torchao.quantization import Int4WeightOnlyConfig
            except ImportError:
                raise ImportError(TORCHAO_MSG)
            group_size = 128
            base_config = Int4WeightOnlyConfig(group_size = group_size)
            filter_fn = (
                lambda m, _: isinstance(m, torch.nn.Linear)
                and m.in_features >= group_size
            )
            torchao_config = TorchAOConfig(
                qat_scheme = qat_scheme,
                base_config_and_filter_fns = [(base_config, filter_fn)],
            )
        elif qat_scheme == "int8":
            try:
                from torchao.quantization import IntxWeightOnlyConfig
                from torchao.quantization.granularity import PerAxis
            except ImportError:
                raise ImportError(TORCHAO_MSG)

            base_config = IntxWeightOnlyConfig(
                weight_dtype = torch.int8,
                granularity = PerAxis(0),
            )
            filter_fn = lambda m, _: isinstance(m, torch.nn.Linear)
            torchao_config = TorchAOConfig(
                qat_scheme = qat_scheme,
                base_config_and_filter_fns = [(base_config, filter_fn)],
            )
        elif qat_scheme == "cactus":
            try:
                from torchao.quantization import IntxWeightOnlyConfig
            except ImportError:
                raise ImportError(TORCHAO_MSG)

            # IntxWeightOnlyConfig already defaults to
            # `mapping_type = MappingType.SYMMETRIC`, so we intentionally do not
            # import `MappingType` here. Matches the upstream Cactus runtime
            # int8 / per-group-32 / symmetric weight-only configuration.
            group_size = 32
            base_config = IntxWeightOnlyConfig(
                weight_dtype = torch.int8,
                granularity = PerGroup(group_size),
            )
            filter_fn = (
                lambda m, _: isinstance(m, torch.nn.Linear)
                and m.in_features >= group_size
                and m.in_features % group_size == 0
            )
            # Warn if any Linear layer is skipped by the cactus filter because
            # its in_features is not divisible by `group_size`. torchao's
            # PerGroup(32) quantizer rejects non-divisible widths at
            # `quantize_()` time, so the filter excludes those layers to keep
            # the QAT prepare step from crashing. Surface that silently-skipped
            # coverage gap to the user so they know some Linears will stay in
            # full precision during training.
            skipped_cactus_layers = [
                name
                for name, module in model.named_modules()
                if isinstance(module, torch.nn.Linear)
                and module.in_features >= group_size
                and module.in_features % group_size != 0
            ]
            if skipped_cactus_layers:
                preview = ", ".join(skipped_cactus_layers[:8])
                if len(skipped_cactus_layers) > 8:
                    preview += f", ... ({len(skipped_cactus_layers) - 8} more)"
                warnings.warn(
                    f"Unsloth: qat_scheme='cactus' uses PerGroup({group_size}) "
                    "which requires in_features to be divisible by "
                    f"{group_size}. The following Linear layers will be kept "
                    f"in full precision during QAT: {preview}",
                    stacklevel = 2,
                )
            torchao_config = TorchAOConfig(
                qat_scheme = qat_scheme,
                base_config_and_filter_fns = [(base_config, filter_fn)],
            )
        else:
            raise ValueError(f"Unexpected QAT scheme {qat_scheme}")
        assert torchao_config is not None, f"TorchAOConfig was not set for {qat_scheme}"
    else:
        torchao_config = qat_scheme

    # Save Torchao metadata everywhere
    inner_model = model
    while hasattr(inner_model, "model"):
        inner_model._torchao_config = torchao_config
        inner_model = inner_model.model
    inner_model._torchao_config = torchao_config

    if torchao_config.prequantization_transform is not None:
        torchao_config.prequantization_transform(model)
    for base_config, filter_fn in torchao_config.base_config_and_filter_fns:
        quantize_(model, QATConfig(base_config, step = "prepare"), filter_fn = filter_fn)

    return model