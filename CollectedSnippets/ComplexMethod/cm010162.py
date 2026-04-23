def retrace_as_exported_program(
        self,
        gm: torch.fx.GraphModule,
        name_to_constant: dict[str, Any],
    ):
        dynamic_shapes = _tree_map_with_path(
            lambda path, x: (
                [Dim.AUTO] * x.dim() if isinstance(x, torch.Tensor) else None
            ),
            self.sample_args,
        )

        # TODO: adjust input orders to match GraphSignature convention
        ep = torch.export._trace._export(
            gm,
            self.sample_args,
            dynamic_shapes=dynamic_shapes,
            strict=False,
            pre_dispatch=True,
        )

        # Post-processing to make sure the ExportedProgram states are correct.
        # Because during conversion, we set tensor constants as GetAttr,
        # retracing cannot recognize them as tensor constants but instead
        # treat them as buffers. We need to set them again here.
        ep._constants.update(
            {
                k: v
                for k, v in name_to_constant.items()
                if isinstance(v, (torch.Tensor, torch.ScriptObject))
            }
        )
        for k in name_to_constant:
            ep.state_dict.pop(k, None)

        for spec in ep.graph_signature.input_specs:
            # Mark as constant tensors for erroneously traced buffers.
            if spec.kind == InputKind.BUFFER and spec.target in name_to_constant:
                if not isinstance(name_to_constant[spec.target], torch.Tensor):
                    raise AssertionError(
                        f"{type(name_to_constant[spec.target])} has been erroneously marked as buffer"
                    )
                spec.kind = InputKind.CONSTANT_TENSOR
                spec.persistent = None
        ep.verifier().check(ep)

        return ep