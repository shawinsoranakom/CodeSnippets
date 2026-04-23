def save_tpu_checkpoint(model, args, accelerator, processing_class, is_fsdp_xla_v1_enabled, output_dir=None):
    """
    Saves a model checkpoint on TPU/XLA devices.

    Handles FSDP v1 sharded checkpoints (with consolidation on master), as well as
    standard XLA model saving via `save_pretrained` or `xm.save`.

    Args:
        model (`torch.nn.Module`): The model to save.
        args (`TrainingArguments`): The training arguments.
        accelerator (`Accelerator`): The accelerator instance.
        processing_class: The processing class (tokenizer/processor) to save alongside the model.
        is_fsdp_xla_v1_enabled (`bool`): Whether FSDP XLA v1 is enabled.
        output_dir (`str`, *optional*): The directory to save to. Defaults to `args.output_dir`.
    """
    import torch_xla.core.xla_model as xm

    output_dir = output_dir if output_dir is not None else args.output_dir

    logger.info(f"Saving model checkpoint to {output_dir}")
    xm.mark_step()

    if xm.is_master_ordinal(local=False):
        os.makedirs(output_dir, exist_ok=True)
        torch.save(args, os.path.join(output_dir, "training_args.bin"))

    # Save a trained model and configuration using `save_pretrained()`.
    # They can then be reloaded using `from_pretrained()`
    supported_classes = (PushToHubMixin,)
    xm.rendezvous("saving_checkpoint")
    if is_fsdp_xla_v1_enabled:
        ckpt = {
            "model": model.state_dict(),
            "shard_metadata": model.get_shard_metadata(),
        }
        ckpt_path = os.path.join(output_dir, f"rank{args.process_index}-of-{args.world_size}-{WEIGHTS_NAME}")
        # All ranks save sharded checkpoint
        xm.save(ckpt, ckpt_path, master_only=False)
        # Make sure all ranks have saved checkpoints
        xm.rendezvous("save_full_checkpoints")
        # Master save full checkpoint
        if args.should_save:
            from torch_xla.distributed.fsdp import consolidate_sharded_model_checkpoints

            full_state_dict, _ = consolidate_sharded_model_checkpoints(
                ckpt_prefix=os.path.join(output_dir, ""),
                ckpt_suffix=f"rank*-of-*-{WEIGHTS_NAME}",
                save_model=False,
            )
            model = model.module.module
            unwrapped_model = accelerator.unwrap_model(model)
            if isinstance(unwrapped_model, supported_classes):
                unwrapped_model.save_pretrained(output_dir, state_dict=full_state_dict)
            else:
                logger.info("Trainer.model is not a `PreTrainedModel`, only saving its state dict.")
                xm.save(full_state_dict, os.path.join(output_dir, WEIGHTS_NAME))
    elif not isinstance(model, supported_classes):
        if isinstance(accelerator.unwrap_model(model), supported_classes):
            accelerator.unwrap_model(model).save_pretrained(
                output_dir,
                is_main_process=args.should_save,
                state_dict=xm._maybe_convert_to_cpu(model.state_dict()),
            )
        else:
            logger.info("Trainer.model is not a `PreTrainedModel`, only saving its state dict.")
            state_dict = xm._maybe_convert_to_cpu(model.state_dict())
            xm.save(state_dict, os.path.join(output_dir, WEIGHTS_NAME))
    else:
        model.save_pretrained(
            output_dir,
            is_main_process=args.should_save,
            state_dict=xm._maybe_convert_to_cpu(model.state_dict()),
        )
    if processing_class is not None and args.should_save:
        processing_class.save_pretrained(output_dir)