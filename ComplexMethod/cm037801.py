def get_expert_weights(self) -> Iterable[torch.Tensor]:
        def _maybe_make_contiguous(
            name: str, p: torch.nn.Parameter
        ) -> torch.nn.Parameter:
            """
            In some cases, the last 2 dimensions (the non-expert dimensions)
            of the weight scale tensor are transposed. This function
            transforms the tensor (view update) so the tensor is contiguous().
            Example: A non-contiguous scale tensor,
              `x` of shape (E, 32, 16) and stride (512, 1, 32) is transformed to
              `x_` of shape (E, 16, 32) and stride (512, 32, 1).
              Note that we specifically use torch.transpose() so `x_` refers
              to the same underlying memory. The tensors `x` and `x_`, pointing
              to the same underlying memory make this transformation safe in the
              context of EPLB. i.e. It is the same memory and just the view
              is different.
            Note: This function handles the "weight_scale" tensors specifically.
            This could however be generalized to handle similar tensors.
            """
            if p.ndim != 3:
                return p
            if p.is_contiguous():
                # Already contiguous. do nothing.
                return p
            # p is non-contiguous. We only handle the case where the last 2
            # dimensions of the scales tensor is transposed. We can handle
            # other cases when they become relevant.
            is_transposed_12 = p.stride(1) == 1 and p.stride(2) != 1
            if "weight_scale" not in name or not is_transposed_12:
                # do nothing.
                return p

            # Do not update the layer parameter as the layer's MoE operations would
            # expect the parameter's tensor to the same shape / stride. Instead,
            # make a new torch.nn.Parameter that is used just in the context of
            # EPLB.
            return torch.nn.Parameter(
                torch.transpose(p.data, 1, 2), requires_grad=False
            )

        weights = list(self.named_parameters())
        weights = [(name, _maybe_make_contiguous(name, p)) for name, p in weights]

        # `w13_input_scale` and `w2_input_scale` are global per-tensor
        # activation scales shared across all experts (e.g. NVFP4).
        # They are broadcast views (stride 0) from .expand() and are
        # not actual expert weights, so exclude them from EPLB.
        NON_EXPERT_WEIGHTS = {
            "e_score_correction_bias",
            "w13_input_scale",
            "w2_input_scale",
        }

        assert all(
            weight.is_contiguous()
            for name, weight in weights
            if not (
                name.startswith("_shared_experts.")
                or name.startswith("_gate.")
                or name.startswith("_routed_input_transform.")
                or name.startswith("_routed_output_transform.")
            )
            and name not in NON_EXPERT_WEIGHTS
        )

        return [
            weight.view(self.local_num_experts, -1)
            for name, weight in weights
            if name not in NON_EXPERT_WEIGHTS
            and weight.shape != torch.Size([])
            and not name.startswith("_shared_experts.")
            # exclude parameters from non-expert submodules,
            # e.g. gate/shared/transforms.
            and not name.startswith("_gate.")
            and not name.startswith("_routed_input_transform.")
            and not name.startswith("_routed_output_transform.")
        ]