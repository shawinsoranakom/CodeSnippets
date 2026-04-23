def check(self, out: tuple[torch.Tensor, ...]) -> None:
        if self.accumulate_grad:
            # Using .backward, graph outputs are empty
            assert not out
            nan_params: list[str] = []
            for inputs_str, param in self.params_to_check.items():
                assert param.grad is not None  # not true for autograd.grad
                if torch.isnan(param.grad).any():
                    nan_params.append(inputs_str)

            if nan_params:
                raise RuntimeError(
                    f"Compiled Autograd returned NaN gradients for parameters: {','.join(nan_params)}."
                )
        else:
            # Using .grad, graph outputs are grads
            nan_grads: list[str] = []
            for i, grad in enumerate(out):
                if torch.isnan(grad).any():
                    nan_grads.append(self.output_names[i])

            if nan_grads:
                raise RuntimeError(
                    f"Compiled Autograd returned NaN gradients for output nodes: {','.join(nan_grads)}."
                )