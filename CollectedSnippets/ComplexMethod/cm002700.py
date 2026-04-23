def validate_quantization_for_training(model):
    """
    Validate that a quantized model is set up correctly for training.

    Raises `ValueError` when:
    - A quantized + compiled model is used (torch.compile is not supported with PEFT fine-tuning).
    - A purely quantized model has no trainable adapters attached (unless it supports QAT).
    - The quantization method does not support training.

    Args:
        model: The model to validate.
    """
    _is_quantized_and_base_model = getattr(model, "is_quantized", False) and not getattr(
        model, "_hf_peft_config_loaded", False
    )
    _quantization_method_supports_training = (
        getattr(model, "hf_quantizer", None) is not None and model.hf_quantizer.is_trainable
    )
    _is_model_quantized_and_qat_trainable = getattr(model, "hf_quantizer", None) is not None and getattr(
        model.hf_quantizer, "is_qat_trainable", False
    )

    # Filter out quantized + compiled models
    if _is_quantized_and_base_model and hasattr(model, "_orig_mod"):
        raise ValueError(
            "You cannot fine-tune quantized model with `torch.compile()` make sure to pass a non-compiled model when fine-tuning a quantized model with PEFT"
        )

    # At this stage the model is already loaded
    if _is_quantized_and_base_model and not _is_peft_model(model) and not _is_model_quantized_and_qat_trainable:
        raise ValueError(
            "You cannot perform fine-tuning on purely quantized models. Please attach trainable adapters on top of"
            " the quantized model to correctly perform fine-tuning. Please see: https://huggingface.co/docs/transformers/peft"
            " for more details"
        )
    elif _is_quantized_and_base_model and not _quantization_method_supports_training:
        raise ValueError(
            f"The model you are trying to fine-tune is quantized with {model.hf_quantizer.quantization_config.quant_method}"
            " but that quantization method do not support training. Please open an issue on GitHub: https://github.com/huggingface/transformers"
            f" to request the support for training support for {model.hf_quantizer.quantization_config.quant_method}"
        )