def test_cuda(self, test_case):
        if not TEST_CUDA or not self.should_test_cuda:
            raise unittest.SkipTest('Excluded from CUDA tests')

        with set_default_dtype(self.default_dtype):
            cpu_input = self._get_input()

            type_map = {torch.double: torch.float}
            cpu_input_tuple = cpu_input if isinstance(cpu_input, tuple) else (cpu_input,)

            is_any_input_complex = any(isinstance(t, torch.Tensor) and t.dtype.is_complex for t in cpu_input_tuple)

            gpu_input_tuple = to_gpu(cpu_input_tuple, type_map=type_map)

            cpu_module = self.constructor(*self.constructor_args)
            gpu_module = self.constructor(*self.constructor_args).float().cuda()
            cpu_param = test_case._get_parameters(cpu_module)
            gpu_param = test_case._get_parameters(gpu_module)
            for cpu_p, gpu_p in zip(cpu_param[0], gpu_param[0], strict=True):
                gpu_p.data.copy_(cpu_p)

            test_case._zero_grad_input(cpu_input_tuple)
            test_case._zero_grad_input(gpu_input_tuple)
            test_case._zero_grad_parameters(cpu_module)
            test_case._zero_grad_parameters(gpu_module)
            cpu_output = test_case._forward(cpu_module, cpu_input_tuple)
            gpu_output = test_case._forward(gpu_module, gpu_input_tuple)
            if getattr(cpu_module, "return_indices", False):
                cpu_output = cpu_output[0]
                gpu_output = gpu_output[0]
            test_case.assertEqual(cpu_output, gpu_output, atol=self.precision, rtol=0, exact_dtype=False)

            # Run backwards on CPU and GPU and compare results
            for _ in range(5):
                cpu_gradOutput = cpu_output.clone().normal_()
                gpu_gradOutput = cpu_gradOutput.type_as(gpu_output)
                cpu_gradInput = test_case._backward(cpu_module, cpu_input_tuple, cpu_output, cpu_gradOutput)
                gpu_gradInput = test_case._backward(gpu_module, gpu_input_tuple, gpu_output, gpu_gradOutput)
                test_case.assertEqual(cpu_gradInput, gpu_gradInput, atol=self.precision, rtol=0, exact_dtype=False)
                for cpu_d_p, gpu_d_p in zip(cpu_param[1], gpu_param[1], strict=True):
                    test_case.assertEqual(cpu_d_p, gpu_d_p, atol=self.precision, rtol=0)

            # Run double-backwards on CPU and GPU and compare results
            if self.check_gradgrad and not self.FIXME_no_cuda_gradgrad_comparison:
                cpu_output = cpu_module(*cpu_input_tuple)
                gpu_output = gpu_module(*gpu_input_tuple)
                if getattr(cpu_module, "return_indices", False):
                    cpu_output = cpu_output[0]
                    gpu_output = gpu_output[0]

                cpu_gradOutput = torch.randn_like(cpu_output, requires_grad=True)
                gpu_gradOutput = cpu_gradOutput.type_as(gpu_output).detach()
                gpu_gradOutput.requires_grad = True

                cpu_gradInputs = torch.autograd.grad(
                    cpu_output,
                    cpu_input_tuple + tuple(cpu_module.parameters()),
                    cpu_gradOutput,
                    create_graph=True)
                gpu_gradInputs = torch.autograd.grad(
                    gpu_output,
                    gpu_input_tuple + tuple(gpu_module.parameters()),
                    gpu_gradOutput,
                    create_graph=True)

                for cpu_d_i, gpu_d_i in zip(cpu_gradInputs, gpu_gradInputs, strict=True):
                    test_case.assertEqual(cpu_d_i, gpu_d_i, atol=self.precision, rtol=0, exact_dtype=False)

                # We mix output into the second backwards computation so that
                # torch.autograd.grad doesn't complain that some inputs
                # are unreachable (which can happen if you differentiate
                # only on the gradient.
                if is_any_input_complex:
                    outputs_cpu = cpu_output.sum().abs() + sum(x.sum().abs() for x in cpu_gradInputs)
                    outputs_gpu = gpu_output.sum().abs() + sum(x.sum().abs() for x in gpu_gradInputs)
                else:
                    outputs_cpu = cpu_output.sum() + sum(x.sum() for x in cpu_gradInputs)
                    outputs_gpu = gpu_output.sum() + sum(x.sum() for x in gpu_gradInputs)

                cpu_gg = torch.autograd.grad(
                    outputs_cpu,
                    cpu_input_tuple + (cpu_gradOutput,) + tuple(cpu_module.parameters()),
                    retain_graph=True)
                gpu_gg = torch.autograd.grad(
                    outputs_gpu,
                    gpu_input_tuple + (gpu_gradOutput,) + tuple(gpu_module.parameters()),
                    retain_graph=True)
                test_case.assertEqual(cpu_gradInput, gpu_gradInput, atol=self.precision, rtol=0, exact_dtype=False)
                for cpu_d_p, gpu_d_p in zip(cpu_gg, gpu_gg, strict=True):
                    test_case.assertEqual(cpu_d_p, gpu_d_p, atol=self.precision, rtol=0, exact_dtype=False)

            self.test_noncontig(test_case, gpu_module, gpu_input_tuple)