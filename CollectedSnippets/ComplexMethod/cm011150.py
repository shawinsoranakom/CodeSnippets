def step(self, gradients: list[Tensor | None]):
        params = self.param_group["params"]
        params_with_grad = []
        grads = []
        momentum_buffer_list: list[Tensor | None] = []
        lr = self.defaults["lr"]
        weight_decay = self.defaults["weight_decay"]
        momentum = self.defaults["momentum"]
        dampening = self.defaults["dampening"]

        if len(params) != len(gradients):
            raise ValueError(
                "the gradients passed in does not equal to the size of the parameters!"
                + f"Params length: {len(params)}. "
                + f"Gradients length: {len(gradients)}"
            )

        has_sparse_grad = False
        for param, gradient in zip(params, gradients):
            if gradient is not None:
                params_with_grad.append(param)
                grads.append(gradient)
                if gradient.is_sparse:
                    has_sparse_grad = True

                if param not in self.state:
                    self.state[param] = {}

                state = self.state[param]
                if "momentum_buffer" not in state:
                    momentum_buffer_list.append(None)
                else:
                    momentum_buffer_list.append(state["momentum_buffer"])

        with torch.no_grad():
            F.sgd(
                params_with_grad,
                grads,
                momentum_buffer_list,
                weight_decay=weight_decay,
                momentum=momentum,
                lr=lr,
                dampening=dampening,
                nesterov=self.nesterov,
                maximize=self.maximize,
                has_sparse_grad=has_sparse_grad,
                foreach=self.foreach,
                fused=self.fused,
                grad_scale=None,
                found_inf=None,
            )

        # update momentum_buffers in state
        for i, p in enumerate(params_with_grad):
            state = self.state[p]
            momentum_buffer = momentum_buffer_list[i]
            if momentum_buffer is not None:
                state["momentum_buffer"] = momentum_buffer