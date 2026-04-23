def _init_group(
        self,
        group,
        params_with_grad,
        grads,
        square_avgs,
        momentum_buffer_list,
        grad_avgs,
        state_steps,
    ):
        has_complex = False
        for p in group["params"]:
            if p.grad is None:
                continue
            has_complex |= torch.is_complex(p)
            params_with_grad.append(p)

            if p.grad.is_sparse:
                raise RuntimeError("RMSprop does not support sparse gradients")
            grads.append(p.grad)

            state = self.state[p]

            # State initialization
            if len(state) == 0:
                state["step"] = (
                    torch.zeros((), dtype=_get_scalar_dtype(), device=p.device)
                    if group["capturable"]
                    else torch.zeros((), dtype=_get_scalar_dtype())
                )
                state["square_avg"] = torch.zeros_like(
                    p, memory_format=torch.preserve_format
                )
                if group["momentum"] > 0:
                    state["momentum_buffer"] = torch.zeros_like(
                        p, memory_format=torch.preserve_format
                    )
                if group["centered"]:
                    state["grad_avg"] = torch.zeros_like(
                        p, memory_format=torch.preserve_format
                    )
            square_avgs.append(state["square_avg"])
            state_steps.append(state["step"])

            if group["momentum"] > 0:
                momentum_buffer_list.append(state["momentum_buffer"])
            if group["centered"]:
                grad_avgs.append(state["grad_avg"])

        return has_complex