def call_trtllm_fused_allreduce_norm(
        allreduce_in: torch.Tensor,
        residual: torch.Tensor,
        rms_gamma: torch.Tensor,
        rms_eps: float,
        world_size: int,
        launch_with_pdl: bool,
        fp32_acc: bool,
        max_token_num: int,
        pattern_code: int,
        norm_out: torch.Tensor | None = None,
        quant_out: torch.Tensor | None = None,
        scale_out: torch.Tensor | None = None,
        scale_factor: torch.Tensor | None = None,
    ) -> None:
        num_tokens, hidden_size = allreduce_in.shape
        element_size = allreduce_in.element_size()
        current_tensor_size = num_tokens * hidden_size * element_size
        max_tensor_size = max_token_num * hidden_size * element_size
        assert current_tensor_size <= max_tensor_size, (
            f"Current tensor size {current_tensor_size} is larger than "
            f"max token num {max_token_num} * hidden size {hidden_size} * "
            f"element size {element_size}"
        )
        curr_device = current_platform.get_device_capability()
        device_capability = curr_device.to_int() if curr_device is not None else None
        # Get one shot input size limit for the current world size
        # for the current device capability
        max_one_shot_size = _FI_ALLREDUCE_ONE_SHOT_MAX_SIZES_MB.get(
            device_capability,  # type: ignore[arg-type, unused-ignore]
            {},
        ).get(world_size, None)
        # Use one shot if no max size is specified
        use_oneshot = (
            max_one_shot_size is None or current_tensor_size <= max_one_shot_size * MiB
        )

        # Select workspace based on pattern: quant patterns use the
        # trtllm quant workspace, non-quant patterns use the primary workspace.
        is_quant_pattern = pattern_code in (
            ar_fusion_patterns.kARResidualRMSNormFP8Quant,
            ar_fusion_patterns.kARResidualRMSNormFP4Quant,
        )
        get_workspace_fn = (
            get_fi_ar_quant_workspace if is_quant_pattern else get_fi_ar_workspace
        )
        workspace = get_workspace_fn(
            world_size=world_size,
            rank=get_tensor_model_parallel_rank(),
            max_token_num=max_token_num,
            hidden_dim=hidden_size,
            dtype=allreduce_in.dtype,
            group=get_tp_group().device_group,
        )
        assert workspace is not None, (
            "Flashinfer allreduce workspace must be initialized when using flashinfer"
        )
        assert flashinfer_comm is not None
        if norm_out is None:
            norm_out = allreduce_in
            residual_out = residual
        else:
            # return residual_out as allreduce_out with zeroed residual_in
            # as flashinfer does not support rms_norm
            # and allreduce_out together
            residual_out = allreduce_in

        layout_code = None
        # layout_code only supported by trtllm backend
        if workspace.backend == "trtllm":
            # in vllm we only support swizzled layout
            layout_code = flashinfer_comm.QuantizationSFLayout.SWIZZLED_128x4

        flashinfer_comm.allreduce_fusion(
            input=allreduce_in,
            workspace=workspace,
            pattern=pattern_code,
            launch_with_pdl=launch_with_pdl,
            output=None,
            residual_out=residual_out,
            norm_out=norm_out,
            quant_out=quant_out,
            scale_out=scale_out,
            residual_in=residual,
            rms_gamma=rms_gamma,
            rms_eps=rms_eps,
            scale_factor=scale_factor,
            layout_code=layout_code,
            use_oneshot=use_oneshot,
            fp32_acc=fp32_acc,
        )