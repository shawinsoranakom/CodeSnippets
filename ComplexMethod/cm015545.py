def get_param_grad_optstate_actual_bytes(
            model: nn.Module, opt: torch.optim.Optimizer
        ) -> tuple[int, int, int]:
            param_bytes = 0
            grad_bytes = 0
            opt_state_bytes = 0
            for param in model.parameters():
                if param.device == dev:
                    param_bytes += param.numel() * param.element_size()
                if param.grad is not None and param.grad.device == dev:
                    grad_bytes += param.grad.numel() * param.grad.element_size()

            for state in opt.state.values():
                for v in state.values():
                    if isinstance(v, torch.Tensor) and v.device == dev:
                        opt_state_bytes += v.numel() * v.element_size()
            return param_bytes, grad_bytes, opt_state_bytes