def apply_grammar_bitmask(
    scheduler_output: SchedulerOutput,
    grammar_output: GrammarOutput,
    input_batch: InputBatch,
    logits: torch.Tensor,
) -> None:
    """
    Apply grammar bitmask to output logits of the model with xgrammar function.

    Args:
        scheduler_output (SchedulerOutput): The result of engine scheduling.
        input_batch (InputBatch): The input of model runner.
        logits (torch.Tensor): The output logits of model forward.
    """
    # Serialization of np.ndarray is much more efficient than a tensor,
    # so we receive it in that format.
    grammar_bitmask = grammar_output.grammar_bitmask

    # We receive the structured output bitmask from the scheduler,
    # compacted to contain bitmasks only for structured output requests.
    # The order of the requests in the bitmask is not guaranteed to be the
    # same as the order of the requests in the gpu runner's batch. We need
    # to sort the bitmask to match the order of the requests used here.

    # Get the batch indices of the structured output requests.
    # Keep track of the number of speculative tokens scheduled for every
    # request in the batch, as the logit indices are offset by this amount.
    struct_out_req_batch_indices: dict[str, int] = {}
    cumulative_offset = 0
    spec_tokens = scheduler_output.scheduled_spec_decode_tokens
    struct_out_req_ids = set(grammar_output.structured_output_request_ids)
    for batch_index, req_id in enumerate(input_batch.req_ids):
        logit_index = batch_index + cumulative_offset
        cumulative_offset += len(spec_tokens.get(req_id, ()))
        if req_id in struct_out_req_ids:
            struct_out_req_batch_indices[req_id] = logit_index

    out_indices = []

    # Reorder the bitmask to match the order of the requests in the batch.
    sorted_bitmask = np.full(
        shape=(logits.shape[0], grammar_bitmask.shape[1]),
        fill_value=-1,
        dtype=grammar_bitmask.dtype,
    )
    cumulative_index = 0
    for req_id in grammar_output.structured_output_request_ids:
        num_spec_tokens = len(spec_tokens.get(req_id, ()))
        if (logit_idx := struct_out_req_batch_indices.get(req_id)) is not None:
            for i in range(1 + num_spec_tokens):
                bitmask_index = logit_idx + i
                sorted_bitmask[bitmask_index] = grammar_bitmask[cumulative_index + i]
                out_indices.append(bitmask_index)
        cumulative_index += 1 + num_spec_tokens

    # Copy async to device as tensor.
    grammar_bitmask = torch.from_numpy(sorted_bitmask).to(
        logits.device, non_blocking=True
    )

    # If the length of out indices and the logits have the same shape
    # we don't need to pass indices to the kernel,
    # since the bitmask is already aligned with the logits.
    skip_out_indices = len(out_indices) == logits.shape[0]

    if not logits.is_cpu:
        index_tensor = None
        if not skip_out_indices:
            # xgrammar expects a python list of indices but it will actually work with
            # a tensor. If we copy the tensor ourselves here we can do it in a
            # non_blocking manner and there should be no cpu sync within xgrammar.
            pin_memory = is_pin_memory_available()
            index_tensor = torch.tensor(
                out_indices, dtype=torch.int32, device="cpu", pin_memory=pin_memory
            )
            index_tensor = index_tensor.to(logits.device, non_blocking=True)

        xgr.apply_token_bitmask_inplace(logits, grammar_bitmask, indices=index_tensor)
        return

    # CPU case, use list for indices.
    indices = None if skip_out_indices else out_indices
    # Handle dtype conversion for CPU (older xgrammar CPU kernels require float32)
    # See: https://github.com/vllm-project/vllm/issues/31901
    if logits.dtype != torch.float32:
        # Convert to float32, apply bitmask, then convert back
        logits_fp32 = logits.to(torch.float32)
        xgr.apply_token_bitmask_inplace(logits_fp32, grammar_bitmask, indices=indices)
        # Copy the modified values back to the original tensor
        logits.copy_(logits_fp32.to(logits.dtype))
    else:
        xgr.apply_token_bitmask_inplace(logits, grammar_bitmask, indices=indices)