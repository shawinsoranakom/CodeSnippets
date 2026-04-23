def _lora_shrink(
    inputs: torch.Tensor,  #  shape [num_tokens, hidden_size]
    lora_a_weights: list[torch.Tensor],  # shape [num_loras, lora_rank, hidden_size]
    output_tensor: torch.Tensor,  # shape [num_slices, num_tokens, lora_rank]
    token_lora_mapping: torch.Tensor,  # shape [num_tokens]
    token_indices_sorted_by_lora_ids: torch.Tensor,  # shape [num_tokens]
    num_tokens_per_lora: torch.Tensor,  # shape [max-loras + 1]
    lora_token_start_loc: torch.Tensor,  # shape [max-loras + 2]
    lora_ids: torch.Tensor,  # shape [max-loras + 1]
    no_lora_flag_cpu: torch.Tensor,  # shape [1]
    num_active_loras: torch.Tensor,  # CPU tensor [1], number of active LoRAs
    scaling: float,
) -> None:
    """
    Args:
        inputs (torch.Tensor): Input tensor
        lora_a_weights (list[torch.Tensor]): LoRA weights
        output_tensor (torch.Tensor): output tensor
        token_lora_mapping (torch.Tensor): A tensor mapping each input token
            to the lora-id related to that token. A value of -1 indicates that
            LoRA doesn't apply to that token.
        token_indices_sorted_by_lora_ids (torch.Tensor): Row/Token indices from
            the A matrix grouped by LoRA IDs.
        num_tokens_per_lora (torch.Tensor): num_tokens_per_lora[i] is the number
            of tokens that are to be processed by LoRA ID lora_ids[i]
        lora_token_start_loc (torch.Tensor): A cumulative sum of
            num_tokens_per_lora. lora_token_start_loc[0] is always 0 so that
            lora_token_start_loc[i], along with num_tokens_per_lora[i]
            identifies the region in token_indices_sorted_by_lora_ids that
            LoRA lora_ids[i] should process.
        lora_ids (torch.Tensor): LoRA ids to process.
        no_lora_flag_cpu (torch.Tensor): A CPU tensor of size 1, that indicates
            if there are any requests that require LoRA.
        num_active_loras (torch.Tensor): A CPU tensor of size 1, containing the
            number of active LoRAs. Stored as a tensor (not int) so
            torch.compile treats it as dynamic rather than a constant.
        scaling (float): Scaling factor.
    """

    assert no_lora_flag_cpu.numel() == 1
    if no_lora_flag_cpu.item():
        # None of the inputs require LoRA.
        return

    assert inputs.dtype == lora_a_weights[0].dtype
    assert inputs.dtype in [torch.float16, torch.bfloat16]
    for weight in lora_a_weights:
        assert weight.dtype in [torch.float16, torch.bfloat16]

    assert inputs.size(1) == lora_a_weights[0].size(-1)
    assert inputs.is_contiguous()
    assert output_tensor.is_contiguous()

    # metadata sanity check
    M = inputs.size(0)
    assert token_lora_mapping.size(0) == M
    assert token_lora_mapping.size(0) == token_indices_sorted_by_lora_ids.size(0)
    assert lora_ids.size(0) == num_tokens_per_lora.size(0)
    assert lora_token_start_loc.size(0) == lora_ids.size(0) + 1

    output_tensor.zero_()

    (lora_ptr_tensor, lora_strides_d0, lora_strides_d1, lora_strides_d2) = (
        _get_lora_a_ptr(lora_a_weights, inputs.device)
    )
    N, K = lora_a_weights[0].shape[-2:]  # K=hidden_size,N=rank
    NUM_SLICES = len(lora_a_weights)
    MAX_LORAS = lora_ids.size(0)

    # Triton kernel configs
    kernel_config = get_lora_op_configs(
        "shrink",
        max_loras=MAX_LORAS,
        batch=M,
        hidden_size=K,
        rank=N,
        num_slices=NUM_SLICES,
    )
    BLOCK_M = kernel_config["block_m"]
    BLOCK_N = kernel_config["block_n"]
    BLOCK_K = kernel_config["block_k"]
    SPLIT_K = kernel_config["split_k"]
    NUM_WARPS = kernel_config["num_warps"]
    NUM_STAGES = kernel_config["num_stages"]
    NUM_CTAS = kernel_config["num_ctas"]
    GROUP_SIZE_M = kernel_config.get("group_size_m", 8)
    EVEN_K = K % (BLOCK_K * SPLIT_K) == 0  # type: ignore

    # TODO (varun): This grid formulation maximizes parallelization at the
    # cost of wasteful thread block launch when only few of the input tokens
    # require LoRA. This might not be the best in all cases.
    grid = (
        SPLIT_K * triton.cdiv(M, BLOCK_M) * triton.cdiv(N, BLOCK_N),
        NUM_SLICES,
        num_active_loras.item(),
    )

    # PDL only works when dual-stream is being used.
    use_gdc = supports_pdl(inputs.device) and envs.VLLM_LORA_ENABLE_DUAL_STREAM
    _lora_shrink_kernel[grid](
        inputs,
        lora_ptr_tensor,
        output_tensor,
        M,
        N,
        K,
        token_indices_sorted_by_lora_ids,
        num_tokens_per_lora,
        lora_token_start_loc,
        lora_ids,
        scaling,
        inputs.stride(0),
        inputs.stride(1),
        lora_strides_d0,
        lora_strides_d1,
        lora_strides_d2,
        output_tensor.stride(0),
        output_tensor.stride(1),
        output_tensor.stride(2),
        BLOCK_M,
        BLOCK_N,
        BLOCK_K,
        EVEN_K,
        SPLIT_K,
        GROUP_SIZE_M,
        NUM_SLICES,
        use_gdc,
        num_warps=NUM_WARPS,
        num_ctas=NUM_CTAS,
        num_stages=NUM_STAGES,
        launch_pdl=use_gdc,
    )

    return