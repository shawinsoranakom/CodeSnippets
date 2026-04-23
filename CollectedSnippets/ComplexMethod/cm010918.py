def _init_group(self, group, params_with_grad, grads, state_sums, state_steps):
        has_sparse_grad, has_complex = False, False
        for p in group["params"]:
            if p.grad is not None:
                if group["fused"] and getattr(
                    self,
                    "_need_device_dtype_check_for_fused",
                    True,
                ):
                    _device_dtype_check_for_fused(p)
                    self._need_device_dtype_check_for_fused = False
                has_sparse_grad |= p.grad.is_sparse
                has_complex |= torch.is_complex(p)
                params_with_grad.append(p)
                grads.append(p.grad)
                state = self.state[p]
                if len(state) == 0:
                    if group["fused"]:
                        _device_dtype_check_for_fused(p)

                    state["step"] = (
                        torch.zeros(
                            (),
                            dtype=_get_scalar_dtype(is_fused=group["fused"]),
                            device=p.device,
                        )
                        if group["fused"]
                        else torch.tensor(0.0, dtype=_get_scalar_dtype())
                    )

                    initial_accumulator_value = self.defaults[
                        "initial_accumulator_value"
                    ]
                    init_value = (
                        complex(initial_accumulator_value, initial_accumulator_value)
                        if torch.is_complex(p)
                        else initial_accumulator_value
                    )
                    state["sum"] = torch.full_like(
                        p, init_value, memory_format=torch.preserve_format
                    )
                state_sums.append(state["sum"])
                state_steps.append(state["step"])

        return has_sparse_grad, has_complex