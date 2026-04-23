def run_grad_conv_test(self, func_forward, func_backward, dim=1, gradient="input"):
        for kern, inp_size in [(3, 6), (3, 7), (4, 9)]:
            for batch, stride, padding, chan_in, chan_out, dilation in product(
                [1, 2], [1, 2], [0, 1, 2], [2], [3], [1]
            ):
                for has_bias in [True, False]:
                    input_shape = [batch, chan_in]
                    weight_shape = [chan_out, chan_in]
                    for _ in range(dim):
                        input_shape.append(inp_size)
                        weight_shape.append(kern)

                    input = torch.randn(input_shape, requires_grad=True)
                    weight = torch.randn(weight_shape, requires_grad=True)
                    if has_bias:
                        bias = torch.randn([chan_out], requires_grad=True)
                    output = func_forward(
                        input,
                        weight,
                        stride=stride,
                        padding=padding,
                        dilation=dilation,
                        bias=bias,
                    )

                    gradient_o = torch.randn(output.shape)
                    gradient_w = torch.autograd.grad(
                        output, input if (gradient == "input") else weight, gradient_o
                    )

                    self.assertEqual(
                        gradient_w[0],
                        func_backward(
                            input_shape if (gradient == "input") else input,
                            weight_shape if (gradient == "weight") else weight,
                            gradient_o,
                            stride=stride,
                            padding=padding,
                            dilation=dilation,
                        ),
                    )