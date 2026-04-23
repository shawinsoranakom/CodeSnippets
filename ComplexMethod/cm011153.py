def step(self, gradients: list[Tensor | None]):
        params = self.param_group["params"]
        params_with_grad = []
        grads = []
        square_avgs = []
        grad_avgs = []
        momentum_buffer_list = []
        state_steps = []
        lr = self.defaults["lr"]
        alpha = self.defaults["alpha"]
        eps = self.defaults["eps"]
        momentum = self.defaults["momentum"]
        weight_decay = self.defaults["weight_decay"]

        if len(params) != len(gradients):
            raise ValueError(
                "the gradients passed in does not equal to the size of the parameters!"
                + f"Params length: {len(params)}. "
                + f"Gradients length: {len(gradients)}"
            )

        has_complex = False
        for param, gradient in zip(params, gradients):
            if gradient is not None:
                has_complex |= torch.is_complex(param)
                params_with_grad.append(param)
                grads.append(gradient)
                # Lazy state initialization
                if param not in self.state:
                    self.state[param] = {}
                    state = self.state[param]
                    state["step"] = torch.tensor(0.0)
                    state["square_avg"] = torch.zeros_like(
                        param, memory_format=torch.preserve_format
                    )
                    if momentum > 0:
                        state["momentum_buffer"] = torch.zeros_like(
                            param, memory_format=torch.preserve_format
                        )
                    if self.centered:
                        state["grad_avg"] = torch.zeros_like(
                            param, memory_format=torch.preserve_format
                        )

                state = self.state[param]
                square_avgs.append(state["square_avg"])
                if momentum > 0:
                    momentum_buffer_list.append(state["momentum_buffer"])
                if self.centered:
                    grad_avgs.append(state["grad_avg"])

                state_steps.append(state["step"])

        with torch.no_grad():
            F.rmsprop(
                params_with_grad,
                grads,
                square_avgs,
                grad_avgs,
                momentum_buffer_list,
                state_steps,
                lr=lr,
                alpha=alpha,
                eps=eps,
                weight_decay=weight_decay,
                momentum=momentum,
                centered=self.centered,
                foreach=self.foreach,
                maximize=self.maximize,
                has_complex=has_complex,
            )