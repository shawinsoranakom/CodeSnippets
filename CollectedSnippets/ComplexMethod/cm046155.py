def step(self, closure=None):
        """Perform a single optimization step.

        Applies either hybrid Muon+SGD updates or pure SGD updates depending on the
        'use_muon' flag in each parameter group. For Muon-enabled groups, parameters
        receive both an orthogonalized Muon update and a standard SGD momentum update.

        Args:
            closure (Callable, optional): A closure that reevaluates the model
                and returns the loss. Default: None.

        Returns:
            (torch.Tensor | None): The loss value if closure is provided, otherwise None.

        Notes:
            - Parameters with None gradients are skipped.
            - Muon updates use Newton-Schulz orthogonalization and work best on 2D+ tensors.
            - Weight decay is applied only to the SGD component in hybrid mode.
        """
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()

        for group in self.param_groups:
            # Muon
            if group["use_muon"]:
                # generate weight updates in distributed fashion
                for p in group["params"]:
                    lr = group["lr"]
                    if p.grad is None:
                        continue
                    grad = p.grad
                    state = self.state[p]
                    if len(state) == 0:
                        state["momentum_buffer"] = torch.zeros_like(p)
                        state["momentum_buffer_SGD"] = torch.zeros_like(p)

                    update = muon_update(
                        grad, state["momentum_buffer"], beta=group["momentum"], nesterov=group["nesterov"]
                    )
                    p.add_(update.reshape(p.shape), alpha=-(lr * self.muon))

                    # SGD update
                    if group["weight_decay"] != 0:
                        grad = grad.add(p, alpha=group["weight_decay"])
                    state["momentum_buffer_SGD"].mul_(group["momentum"]).add_(grad)
                    sgd_update = (
                        grad.add(state["momentum_buffer_SGD"], alpha=group["momentum"])
                        if group["nesterov"]
                        else state["momentum_buffer_SGD"]
                    )
                    p.add_(sgd_update, alpha=-(lr * self.sgd))
            else:  # SGD
                for p in group["params"]:
                    lr = group["lr"]
                    if p.grad is None:
                        continue
                    grad = p.grad
                    if group["weight_decay"] != 0:
                        grad = grad.add(p, alpha=group["weight_decay"])
                    state = self.state[p]
                    if len(state) == 0:
                        state["momentum_buffer"] = torch.zeros_like(p)
                    state["momentum_buffer"].mul_(group["momentum"]).add_(grad)
                    update = (
                        grad.add(state["momentum_buffer"], alpha=group["momentum"])
                        if group["nesterov"]
                        else state["momentum_buffer"]
                    )
                    p.add_(update, alpha=-lr)
        return loss