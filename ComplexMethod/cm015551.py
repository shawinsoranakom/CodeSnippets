def _run_reference_microbatched(
        self,
        ref_model: NormMLPStack,
        input_dt: DTensor,
        target_dt: DTensor,
        *,
        null_boundary_grads: bool = True,
    ) -> tuple[
        dict[str, torch.Tensor | None],
        StageStaticMetaMap,
    ]:
        ref_model.zero_grad(set_to_none=True)

        input_chunks = torch.tensor_split(input_dt, n_microbatches)
        target_chunks = torch.tensor_split(target_dt, n_microbatches)

        captured_io: dict[int, tuple[DTensor, DTensor]] = {}
        captured_grads: dict[int, dict[str, DTensor | None]] = {}
        hooks: list[torch.utils.hooks.RemovableHandle] = []

        def _make_grad_hook(stage_idx: int, key: str) -> Callable[[torch.Tensor], None]:
            def _hook(grad: torch.Tensor) -> None:
                captured_grads[stage_idx][key] = self._clone_preserving_placement(grad)

            return _hook

        for stage_idx, stage_mod in enumerate(ref_model.layers):

            def _capture_io(
                _module: nn.Module,
                args: tuple[torch.Tensor, ...],
                output: torch.Tensor,
                *,
                idx: int = stage_idx,
            ) -> None:
                stage_input = cast(DTensor, args[0])
                stage_output = cast(DTensor, output)
                captured_io[idx] = (stage_input, stage_output)
                captured_grads[idx] = {"input": None, "output": None}

                for tensor, key in (
                    (stage_input, "input"),
                    (stage_output, "output"),
                ):
                    if tensor.requires_grad:
                        hooks.append(tensor.register_hook(_make_grad_hook(idx, key)))

            hooks.append(stage_mod.register_forward_hook(_capture_io))

        static_stage_meta: StageStaticMetaMap = {}

        for mb_idx, (input_chunk, target_chunk) in enumerate(
            zip(input_chunks, target_chunks)
        ):
            output = ref_model(input_chunk)
            loss = _loss_fn(output, target_chunk)
            loss.backward()

            if mb_idx == 0:
                for stage_idx in range(len(ref_model.layers)):
                    stage_input, stage_output = captured_io[stage_idx]
                    input_args = self._empty_dt_from(
                        stage_input,
                        stage_input.requires_grad,
                    )
                    output_args = self._empty_dt_from(
                        stage_output,
                        stage_output.requires_grad,
                    )
                    input_grad_dt = captured_grads[stage_idx]["input"]
                    output_grad_dt = captured_grads[stage_idx]["output"]
                    input_grads = (
                        self._empty_dt_from(cast(DTensor, input_grad_dt), False)
                        if input_grad_dt is not None
                        else None
                    )
                    output_grads = (
                        self._empty_dt_from(cast(DTensor, output_grad_dt), False)
                        if output_grad_dt is not None
                        else None
                    )

                    if null_boundary_grads:
                        if stage_idx == 0:
                            input_grads = None
                        if stage_idx == (len(ref_model.layers) - 1):
                            output_grads = None

                    static_stage_meta[stage_idx] = (
                        input_args,
                        output_args,
                        input_grads,
                        output_grads,
                    )

                for hook in hooks:
                    hook.remove()
                hooks = []

        for param in ref_model.parameters():
            if param.grad is not None:
                param.grad.div_(n_microbatches)

        ref_grads = {
            name: self._clone_preserving_placement(grad) if grad is not None else grad
            for name, grad in (
                (param_name, param.grad)
                for param_name, param in ref_model.named_parameters()
            )
        }
        return ref_grads, static_stage_meta