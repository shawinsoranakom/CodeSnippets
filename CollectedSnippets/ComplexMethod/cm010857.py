def finalize(self, ctx: Any, fw_outs: Sequence[Any]) -> tuple[Any, ...]:
        num_outputs = self.metadata.num_outputs
        num_outputs_aliased = self.metadata.num_outputs_aliased
        num_mutated_runtime_inps = self.metadata.num_mutated_inp_runtime_indices
        num_forward_returns = self.metadata.num_forward_returns

        raw_returns = list(fw_outs[:num_forward_returns])

        # Wrap all autograd.Function.forward() outputs that are aliases
        # so that autograd.Function doesn't treat them as tensors
        if num_mutated_runtime_inps > 0:
            for i, idx in enumerate(self.metadata.mutated_inp_runtime_indices):
                # We could make this faster by only looping over inputs with metadata-only mutations
                # (instead of looping over inputs with either data or metadata mutations), but there shouldn't be many.
                info = self.metadata.input_info[idx]
                if info.mutates_metadata and not info.mutates_data:
                    raw_returns[i] = TensorAlias(raw_returns[i])

            if config.debug_assert:
                user_mutated_inputs_raw = raw_returns[0:num_mutated_runtime_inps]
                mut_inp_infos = [
                    x
                    for x in self.metadata.input_info
                    if x.mutates_data or x.mutates_metadata
                ]
                if len(user_mutated_inputs_raw) != len(mut_inp_infos):
                    raise AssertionError(
                        "expected len(user_mutated_inputs_raw) == len(mut_inp_infos), "
                        f"got {len(user_mutated_inputs_raw)} != {len(mut_inp_infos)}"
                    )

        if self.metadata.num_unsafe_view_outputs > 0:
            for idx in self.metadata.unsafe_view_out_indices:
                raw_return_idx = num_mutated_runtime_inps + idx
                o = raw_returns[raw_return_idx]
                raw_returns[raw_return_idx] = torch.ops.aten._unsafe_view(o, o.shape)

        if num_outputs_aliased > 0:
            for idx in self.metadata.aliased_out_indices:
                raw_return_idx = num_mutated_runtime_inps + idx
                raw_returns[raw_return_idx] = TensorAlias(raw_returns[raw_return_idx])

            if config.debug_assert:
                intermediates_raw = raw_returns[
                    num_mutated_runtime_inps + num_outputs :
                ]
                if any(isinstance(x, TensorAlias) for x in intermediates_raw):
                    raise AssertionError("expected no TensorAlias in intermediates_raw")

        # invariant: intermediate bases always require gradients, so we don't have to
        # consider marking them as non-differentiable.
        raw_returns_not_including_intermediate_bases = raw_returns[
            : num_mutated_runtime_inps + num_outputs
        ]
        raw_returns_meta = [
            x
            for x in self.metadata.input_info
            if x.mutation_type == MutationType.MUTATED_OUT_GRAPH
        ] + self.metadata.output_info

        fw_outs_not_requiring_grad = [
            x
            for (i, x) in enumerate(raw_returns_not_including_intermediate_bases)
            if isinstance(x, torch.Tensor) and not raw_returns_meta[i].requires_grad
        ]
        ctx.mark_non_differentiable(*fw_outs_not_requiring_grad)
        ctx._materialize_non_diff_grads = False
        return tuple(raw_returns)