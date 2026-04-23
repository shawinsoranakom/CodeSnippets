def test_noncontig(self, test_case, module, input):
        # check no scalars, can't make non-contig
        if isinstance(input, torch.Tensor) and input.dim() == 0:
            return
        if any(i.dim() == 0 for i in input if isinstance(i, torch.Tensor)):
            return

        test_case._zero_grad_parameters(module)
        test_case._zero_grad_input(input)
        with freeze_rng_state():
            output = test_case._forward(module, input)
            if getattr(module, "return_indices", False):
                output = output[0]
            grad_output = output.new(output.shape).normal_()
            output = output.clone()
            d_input = deepcopy(test_case._backward(module, input, output, grad_output))
            d_param = deepcopy(test_case._get_parameters(module)[1])

        nc_input = self.noncontiguize(input)
        nc_grad_output = self.noncontiguize(grad_output)
        for contig_i, contig_g in product((True, False), repeat=2):
            i = input if contig_i else nc_input
            # Some ops, e.g., nn.Flatten, return gradient that shares
            # storage with the grad_output. Hence we copy here.
            go = deepcopy(grad_output if contig_g else nc_grad_output)
            test_case._zero_grad_parameters(module)
            test_case._zero_grad_input(i)
            with freeze_rng_state():
                out = test_case._forward(module, i)
                if getattr(module, "return_indices", False):
                    out = out[0]
                grad = test_case._backward(module, i, out, go)

                test_case.assertEqual(out, output)
                test_case.assertEqual(grad, d_input, atol=1e-4, rtol=0)
                test_case.assertEqual(test_case._get_parameters(module)[1], d_param)