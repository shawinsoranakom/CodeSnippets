def _unsloth_save_torchao_with_given_config(
    model,
    save_directory: Union[str, os.PathLike],
    tokenizer,
    torchao_config,
    push_to_hub: bool = False,
    token: Optional[Union[str, bool]] = None,
):
    """Quantizes the model with torchao and saves a torchao quantized checkpoint

    Args
      `save_directory`: local folder path or huggingface hub ID when `push_to_hub` is set to True, e.g. `my_model`
      `torchao_config` (TorchAOBaseConfig): configuration for torchao quantization, full list: https://docs.pytorch.org/ao/main/api_ref_quantization.html#inference-apis-for-quantize
      `push_to_hub` (bool): whether to push the checkpoint to huggingface hub or save locally
    """

    if push_to_hub:
        assert token is not None, "Unsloth: Please specify a token for uploading!"

    assert (
        torchao_config is not None
    ), "Unsloth: Please specify a torchao_config for post-training quantization!"

    # first merge the lora weights
    arguments = dict(locals())
    arguments["push_to_hub"] = False  # We save ourselves
    arguments["save_method"] = "merged_16bit"  # Must be 16bit
    del arguments["torchao_config"]

    if not isinstance(model, PeftModelForCausalLM) and not isinstance(model, PeftModel):
        model.save_pretrained(save_directory)
        tokenizer.save_pretrained(save_directory)
    else:
        unsloth_generic_save(**arguments)

    for _ in range(3):
        gc.collect()

    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        TorchAoConfig,
        AutoModelForImageTextToText,
        AutoProcessor,
    )
    from torchao import quantize_

    if isinstance(torchao_config, TorchAoConfig):
        quantization_config = torchao_config
    else:
        quantization_config = TorchAoConfig(quant_type = torchao_config)

    # Determine if this is a VLM
    is_vlm = False
    if hasattr(model, "config") and hasattr(model.config, "architectures"):
        is_vlm = any(
            x.endswith(("ForConditionalGeneration", "ForVisionText2Text"))
            for x in model.config.architectures
        )
        is_vlm = is_vlm or hasattr(model.config, "vision_config")
    auto_model = AutoModelForImageTextToText if is_vlm else AutoModelForCausalLM
    auto_processor = AutoProcessor if is_vlm else AutoTokenizer

    tokenizer = auto_processor.from_pretrained(save_directory)
    if isinstance(tokenizer, (PreTrainedTokenizerBase, ProcessorMixin)):
        tokenizer = patch_saving_functions(tokenizer)

    # TorchAO must only use bfloat16 for loading (float16 fails)
    if HAS_TORCH_DTYPE:
        kwargs = {"torch_dtype": torch.bfloat16}
    else:
        kwargs = {"dtype": torch.bfloat16}

    # Reload with quantization applied
    quantized_model = auto_model.from_pretrained(
        save_directory,
        device_map = "auto",
        quantization_config = quantization_config,
        **kwargs,
    )

    torchao_save_directory = save_directory + "-torchao"

    # TorchAO does not support safe_serialization right now 0.14.0 seems broken!
    safe_serialization = Version(importlib_version("torchao")) > Version("0.14.0")
    safe_serialization = False

    if push_to_hub:
        quantized_model.push_to_hub(
            torchao_save_directory, safe_serialization = safe_serialization, token = token
        )
        tokenizer.push_to_hub(torchao_save_directory, token = token)
    else:
        quantized_model.save_pretrained(
            torchao_save_directory, safe_serialization = safe_serialization
        )
        tokenizer.save_pretrained(torchao_save_directory, token = token)

    # Clean up the intermediate unquantized model
    if os.path.exists(save_directory):
        try:
            shutil.rmtree(save_directory)
        except:
            pass