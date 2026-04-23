def _codegen_finalize(ctx: Any, fw_outs: Any) -> tuple[Any, ...]:
            num_forward_returns = fw_metadata.num_forward_returns
            raw_returns = list(fw_outs[:num_forward_returns])
            fw_outs_not_requiring_grad = _codegen_transform_raw_returns(raw_returns)
            if config.debug_assert:
                if num_mutated_runtime_inps > 0:
                    user_mutated_inputs_raw = raw_returns[0:num_mutated_runtime_inps]
                    mut_inp_infos = [
                        x
                        for x in fw_metadata.input_info
                        if x.mutates_data or x.mutates_metadata
                    ]
                    if len(user_mutated_inputs_raw) != len(mut_inp_infos):
                        raise AssertionError(
                            f"expected len(user_mutated_inputs_raw) == len(mut_inp_infos), "
                            f"got {len(user_mutated_inputs_raw)} != {len(mut_inp_infos)}"
                        )
                if num_outputs_aliased > 0:
                    intermediates_raw = raw_returns[
                        num_mutated_runtime_inps + num_outputs :
                    ]
                    if any(isinstance(x, TensorAlias) for x in intermediates_raw):
                        raise AssertionError(
                            "expected no TensorAlias in intermediates_raw"
                        )
            ctx.mark_non_differentiable(*fw_outs_not_requiring_grad)
            ctx._materialize_non_diff_grads = False
            return tuple(raw_returns)