def deepspeed_sp_compute_loss(accelerator, model, inputs, return_outputs, pc):
    """
    Computes the loss under sequence parallelism with `sp_backend="deepspeed"` and `sp_size > 1`.

    Performs weighted loss aggregation across SP ranks, accounting for varying numbers of valid tokens per rank
    (e.g., when some ranks receive only padding or prompt tokens that are masked with -100).

    Args:
        accelerator (`Accelerator`): The accelerator instance with `torch_device_mesh` support.
        model (`torch.nn.Module`): The model to compute the loss for.
        inputs (`dict[str, torch.Tensor | Any]`): The input data for the model. Must include `"shift_labels"` key.
        return_outputs (`bool`): Whether to return the model outputs along with the loss.
        pc (`accelerate.parallelism_config.ParallelismConfig`): The parallelism configuration.

    Returns:
        The loss, or a tuple of `(loss, outputs)` if `return_outputs` is `True`.
    """
    # DeepSpeed SP automatically injects shift_labels into inputs (pre-shifted labels for SP).
    # The model's forward pass receives shift_labels via **kwargs and passes it to the loss function.
    # Both standard transformer models and Liger-patched models handle shift_labels correctly,
    # so we can directly use the computed loss from the model output.
    # See: https://huggingface.co/docs/accelerate/en/concept_guides/sequence_parallelism
    if "labels" not in inputs and "shift_labels" in inputs:
        # DeepSpeed SP Dataloader removes "labels" but we need it, otherwise, we won't compute the loss.
        inputs["labels"] = inputs["shift_labels"]
    outputs = model(**inputs)
    loss = outputs.loss

    # Prefer DeepSpeed SP groups when using Ulysses; otherwise fall back to torch device mesh.
    if pc.sp_backend == "deepspeed" and pc.sp_size > 1:
        from deepspeed.utils import groups

        sp_group = groups._get_sequence_parallel_group()
    elif accelerator.torch_device_mesh is not None:
        sp_group = accelerator.torch_device_mesh["sp"].get_group()
    else:
        raise ValueError(
            "Sequence parallelism is enabled but no SP process group is available. "
            "Ensure torch_device_mesh is initialized or sp_backend='deepspeed' with sp_size > 1."
        )
    sp_world_size = pc.sp_size
    # differentiable weighted per-shard-loss aggregation across ranks
    losses_per_rank = torch.distributed.nn.functional.all_gather(loss, group=sp_group)
    # special dealing with SFT that has prompt tokens that aren't used in loss computation
    good_tokens = (inputs["shift_labels"] != -100).view(-1).sum()
    good_tokens_per_rank = torch.distributed.nn.functional.all_gather(good_tokens, group=sp_group)
    # Skip ranks with zero valid tokens
    total_loss = sum(
        losses_per_rank[rank] * good_tokens_per_rank[rank]
        for rank in range(sp_world_size)
        if good_tokens_per_rank[rank] > 0
    )
    total_good_tokens = sum(good_tokens_per_rank)
    loss = total_loss / max(total_good_tokens, 1)

    return (loss, outputs) if return_outputs else loss