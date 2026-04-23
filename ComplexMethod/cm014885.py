def _linear_helper(self, in_features, out_features, shape, bias=True, backward_pass=False):
        cpu_linear = torch.nn.Linear(in_features=in_features, out_features=out_features, device="cpu", bias=bias)
        mps_linear = torch.nn.Linear(in_features=in_features, out_features=out_features, device="mps", bias=bias)

        # Use the same weights and bias as the ones from the cpu
        mps_linear.weight.data = cpu_linear.weight.data.detach().clone().to("mps")

        if bias:
            mps_linear.bias.data = cpu_linear.bias.data.detach().clone().to("mps")

        linear_mps_input = torch.randn(shape).to('mps')
        linear_cpu_input = linear_mps_input.detach().clone().to('cpu')

        if backward_pass:
            linear_mps_input = linear_mps_input.requires_grad_()
            linear_cpu_input = linear_cpu_input.requires_grad_()

        linear_cpu_output = cpu_linear(linear_cpu_input)
        linear_mps_output = mps_linear(linear_mps_input)

        self.assertEqual(linear_cpu_output, linear_mps_output.to('cpu'))
        self.assertEqual(linear_cpu_output.size(), linear_mps_output.size())

        if backward_pass:
            cpu_grad = torch.rand_like(linear_cpu_output, requires_grad=True)
            grad = cpu_grad.detach().to('mps').requires_grad_()

            linear_cpu_output.backward(gradient=cpu_grad, create_graph=True)
            linear_mps_output.backward(gradient=grad, create_graph=True)

            self.assertEqual(linear_cpu_input.grad.size(), linear_mps_input.grad.size())
            self.assertEqual(linear_cpu_input.grad, linear_mps_input.grad.to("cpu"), atol=8e-04, rtol=10.4e-05)

            self.assertEqual(cpu_linear.weight.grad.size(), mps_linear.weight.grad.size())
            self.assertEqual(cpu_linear.weight.grad, mps_linear.weight.grad.to("cpu"), atol=8e-04, rtol=10.4e-05)
            if bias:
                self.assertEqual(cpu_linear.bias.grad.size(), mps_linear.bias.grad.size())
                self.assertEqual(cpu_linear.bias.grad, mps_linear.bias.grad.to("cpu"), atol=8e-04, rtol=10.4e-05)

            # test gradgrad
            x_grad_out = torch.rand_like(linear_cpu_input)
            x_grad_out_mps = x_grad_out.to("mps")
            w_grad_out = torch.rand_like(cpu_linear.weight)
            w_grad_out_mps = w_grad_out.to("mps")

            linear_cpu_input.grad.detach().zero_()
            linear_mps_input.grad.detach().zero_()
            cpu_linear.weight.grad.detach().zero_()
            mps_linear.weight.grad.detach().zero_()
            if bias:
                b_grad_out = torch.rand_like(cpu_linear.bias)
                b_grad_out_mps = b_grad_out.to("mps")
                cpu_linear.bias.grad.detach().zero_()
                mps_linear.bias.grad.detach().zero_()

            linear_cpu_input.grad.backward(x_grad_out, retain_graph=True)
            linear_mps_input.grad.backward(x_grad_out_mps, retain_graph=True)
            cpu_linear.weight.grad.backward(w_grad_out, retain_graph=True)
            mps_linear.weight.grad.backward(w_grad_out_mps, retain_graph=True)
            if bias:
                cpu_linear.bias.grad.backward(b_grad_out, retain_graph=True)
                mps_linear.bias.grad.backward(b_grad_out_mps, retain_graph=True)

            self.assertEqual(cpu_grad.grad, grad.grad)
            self.assertEqual(linear_cpu_input.grad, linear_mps_input.grad)
            self.assertEqual(cpu_linear.weight.grad, mps_linear.weight.grad)
            if bias:
                self.assertEqual(cpu_linear.bias.grad, mps_linear.bias.grad)