def unsloth_generic_save(
    model,
    tokenizer,
    save_directory: Union[str, os.PathLike] = "unsloth_finetuned_merge",
    save_method: str = "lora",  # ["lora", "merged_16bit", "merged_4bit"]
    push_to_hub: bool = False,
    token: Optional[Union[str, bool]] = None,
    is_main_process: bool = True,
    state_dict: Optional[dict] = None,
    save_function: Callable = torch.save,
    max_shard_size: Union[int, str] = "5GB",
    safe_serialization: bool = True,
    variant: Optional[str] = None,
    save_peft_format: bool = True,
    # Push to hub
    use_temp_dir: Optional[bool] = None,
    commit_message: Optional[str] = "Trained with Unsloth",
    private: Optional[bool] = None,
    create_pr: bool = False,
    revision: str = None,
    commit_description: str = "Upload model trained with Unsloth 2x faster",
    tags: List[str] = None,
    # Our functions
    temporary_location: str = "_unsloth_temporary_saved_buffers",
    maximum_memory_usage: float = 0.9,
    datasets: Optional[List[str]] = None,
):
    if isinstance(tokenizer, (PreTrainedTokenizerBase, ProcessorMixin)):
        tokenizer = patch_saving_functions(tokenizer)

    if token is None and push_to_hub:
        token = get_token()

    if save_method == "merged_4bit":
        raise RuntimeError(
            "Unsloth: Merging into 4bit will cause your model to lose accuracy if you plan\n"
            "to merge to GGUF or others later on. I suggest you to do this as a final step\n"
            "if you're planning to do multiple saves.\n"
            "If you are certain, change `save_method` to `merged_4bit_forced`."
        )
    elif save_method == "merged_4bit_forced":
        save_method = "merged_4bit"

    # Full-finetuned models (no LoRA) cannot use merge_and_overwrite_lora
    # since there are no adapters to merge. Fall back to save_pretrained.
    # This mirrors the non-PeftModel handling in save_pretrained_torchao
    # and the GGUF save path.
    _is_peft = isinstance(model, PeftModel)
    if not _is_peft:
        if not is_main_process:
            return

        # Honor merged_16bit by casting to the target dtype if needed
        _save_kwargs = dict(
            safe_serialization = safe_serialization,
            max_shard_size = max_shard_size,
            variant = variant,
        )
        if "16bit" in save_method:
            _target_dtype = (
                torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
            )
            _save_kwargs["state_dict"] = {
                k: v.to(dtype = _target_dtype) if v.is_floating_point() else v
                for k, v in model.state_dict().items()
            }

        if push_to_hub:
            print(f"Unsloth: Pushing full fine-tuned model to '{save_directory}' ...")
            model.push_to_hub(
                repo_id = save_directory,
                token = token,
                private = private,
                commit_message = commit_message,
                create_pr = create_pr,
                revision = revision,
                commit_description = commit_description,
                tags = tags,
                **_save_kwargs,
            )
            if tokenizer is not None:
                _tokenizer = (
                    tokenizer.tokenizer
                    if hasattr(tokenizer, "tokenizer")
                    else tokenizer
                )
                old_padding_side = _tokenizer.padding_side
                _tokenizer.padding_side = "left"
                tokenizer.push_to_hub(
                    save_directory,
                    token = token,
                    private = private,
                    commit_message = commit_message,
                    create_pr = create_pr,
                    revision = revision,
                )
                _tokenizer.padding_side = old_padding_side
        else:
            print(f"Unsloth: Saving full fine-tuned model to '{save_directory}' ...")
            model.save_pretrained(save_directory, **_save_kwargs)
            if tokenizer is not None:
                _tokenizer = (
                    tokenizer.tokenizer
                    if hasattr(tokenizer, "tokenizer")
                    else tokenizer
                )
                old_padding_side = _tokenizer.padding_side
                _tokenizer.padding_side = "left"
                tokenizer.save_pretrained(save_directory)
                _tokenizer.padding_side = old_padding_side

        print(f"Unsloth: Model saved successfully to '{save_directory}'")
    else:
        merge_and_overwrite_lora(
            get_model_name,
            model = model,
            tokenizer = tokenizer,
            save_directory = save_directory,
            push_to_hub = push_to_hub,
            private = private,
            token = token,
            save_method = save_method,
            output_dtype = None,
            low_disk_space_usage = True,
            use_temp_file = False,
        )

    if push_to_hub and datasets:
        try:
            from huggingface_hub import metadata_update

            save_dir, _ = _determine_username(save_directory, None, token)
            metadata_update(
                save_dir, {"datasets": datasets}, overwrite = True, token = token
            )
        except Exception as e:
            logger.warning_once(
                f"Unsloth: Could not update datasets metadata for {save_directory}: {e}"
            )

    return