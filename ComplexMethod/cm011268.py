def __init__(
        self,
        submodule: nn.Module,
        stage_index: int,
        num_stages: int,
        device: torch.device,
        input_args: torch.Tensor | tuple[torch.Tensor, ...] | None = None,
        output_args: torch.Tensor | tuple[torch.Tensor, ...] | None = None,
        output_grads: torch.Tensor | tuple[torch.Tensor | None, ...] | None = None,
        input_grads: torch.Tensor | tuple[torch.Tensor | None, ...] | None = None,
        group: dist.ProcessGroup | None = None,
        dw_builder: Callable[[], Callable[..., None]] | None = None,
        get_mesh: GetMeshCallback | None = None,
    ):
        super().__init__(submodule, stage_index, num_stages, device, group, dw_builder)

        self._mesh_cache = _MeshCache(get_mesh_cb=get_mesh)
        self._inference_mode: InferenceMode | None = None
        self._fwd_outputs_for_bwd_meta: tuple[torch.Tensor, ...] | None = None
        self._fwd_inputs_for_bwd_meta: tuple[torch.Tensor, ...] | None = None
        self._fwd_kwargs_tensors_for_bwd_meta: tuple[torch.Tensor, ...] | None = None

        # Validate and normalize args to tuples
        inputs = validate_and_normalize_to_tuple(input_args)
        outputs = validate_and_normalize_to_tuple(output_args)
        in_grads = validate_and_normalize_to_tuple(input_grads, allow_none=True)
        out_grads = validate_and_normalize_to_tuple(output_grads, allow_none=True)

        self._user_meta = _StageMeta(
            inputs=extract_tensor_metas(inputs),
            outputs=extract_tensor_metas(outputs),
            input_grads=extract_tensor_metas(in_grads, allow_none=True),
            output_grads=extract_tensor_metas(out_grads, allow_none=True),
        )

        # Cache meshes from user-provided DTensors
        for args in (inputs, outputs, in_grads, out_grads):
            if args is not None:
                self._mesh_cache.update_from_tensors(args)

        # Validate DTensor↔grad correspondence independently for inputs and outputs
        if self._user_meta.has_dtensors():
            if inputs and in_grads:
                validate_static_arg_grad_correspondence(
                    self.stage_index, inputs, in_grads, is_input=True
                )
            if outputs and out_grads:
                validate_static_arg_grad_correspondence(
                    self.stage_index, outputs, out_grads, is_input=False
                )