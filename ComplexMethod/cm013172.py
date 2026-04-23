def _analytical_jacobian(self, module, input: _TensorOrTensors, jacobian_input=True, jacobian_parameters=True):
        output = self._forward(module, input)
        output_size = output.nelement()

        if jacobian_input:
            jacobian_inp = self._jacobian(input, output_size)
            flat_jacobian_input = list(_iter_tensors(jacobian_inp))

        if jacobian_parameters:
            num_param = sum(p.numel() for p in self._get_parameters(module)[0])
            jacobian_param = torch.zeros(num_param, output_size)

        for i in range(output_size):
            param, d_param = self._get_parameters(module)
            # make non grad zeros
            d_param = [torch.zeros_like(p) if d is None else d for (p, d) in zip(param, d_param, strict=True)]

            d_out = torch.zeros_like(output)
            flat_d_out = d_out.view(-1)
            flat_d_out[i] = 1

            if jacobian_parameters:
                self._zero_grad_parameters(module)
            # Tensors will accumulate gradient from multiple steps
            if jacobian_input:
                self._zero_grad_input(input)
            d_input = self._backward(module, input, output, d_out)

            if jacobian_input:
                for jacobian_x, d_x in zip(flat_jacobian_input, _iter_tensors(d_input), strict=True):
                    jacobian_x[:, i] = d_x.contiguous().view(-1)
            if jacobian_parameters:
                jacobian_param[:, i] = torch.cat(self._flatten_tensors(d_param), 0)

        res: tuple[torch.Tensor, ...] = ()
        if jacobian_input:
            res += jacobian_inp,
        if jacobian_parameters:
            res += jacobian_param,

        return res