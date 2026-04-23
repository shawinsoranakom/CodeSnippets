def unsloth_save_pretrained_torchao(
    self,
    save_directory: Union[str, os.PathLike],
    tokenizer = None,
    torchao_config = None,
    push_to_hub: bool = False,
    token: Optional[Union[str, bool]] = None,
):
    """Saves a torchao quantized model checkpoint.

    This function handles two mutually exclusive workflows:

    1. **QAT (Quantization-Aware Training)**: If the model was trained with `qat_scheme`
       parameter, do NOT pass `torchao_config`. The function will convert the QAT
       fake-quantized weights to real quantized weights and save directly.

    2. **PTQ (Post-Training Quantization)**: If you want to apply quantization to a
       regular model, pass a `torchao_config`. The model must NOT have been trained
       with `qat_scheme`.

    Args:
      `save_directory`: local folder path or huggingface hub ID when `push_to_hub` is True
      `tokenizer`: the tokenizer to save alongside the model
      `torchao_config` (TorchAOBaseConfig): configuration for torchao quantization.
          Required for PTQ, must be None for QAT models.
          Options: https://docs.pytorch.org/ao/main/api_ref_quantization.html#inference-apis-for-quantize
      `push_to_hub` (bool): whether to push to huggingface hub or save locally
      `token`: HuggingFace token for pushing to hub
    """
    if isinstance(tokenizer, (PreTrainedTokenizerBase, ProcessorMixin)):
        tokenizer = patch_saving_functions(tokenizer)

    if token is None and push_to_hub:
        token = get_token()

    has_qat_config = (
        hasattr(self, "_torchao_config") and self._torchao_config is not None
    )

    if torchao_config is not None:
        # PTQ path: user provided a config, model must NOT have QAT config unless PEFT
        assert not has_qat_config, (
            "Unsloth: You passed `torchao_config` but this model was trained with `qat_scheme`. "
            "For QAT models, do not pass `torchao_config` - the quantization config is already "
            "attached to the model from training."
        )
        _unsloth_save_torchao_with_given_config(
            model = self,
            save_directory = save_directory,
            tokenizer = tokenizer,
            torchao_config = torchao_config,
            push_to_hub = push_to_hub,
            token = token,
        )
    else:
        # QAT path: no config provided, model must have QAT config
        assert has_qat_config, (
            "Unsloth: No `torchao_config` provided and model was not trained with `qat_scheme`. "
            "Either train with `qat_scheme` parameter, or provide a `torchao_config` for "
            "post-training quantization."
        )
        _unsloth_save_torchao_with_attached_config(
            model = self,
            save_directory = save_directory,
            tokenizer = tokenizer,
            push_to_hub = push_to_hub,
            token = token,
        )

    for _ in range(3):
        gc.collect()