def test_cuda(self, test_case, dtype, extra_args=None):
        def convert_dtype(obj, dtype, requires_grad=False):
            if isinstance(obj, torch.Tensor):
                return obj.detach().to(dtype=dtype).requires_grad_(requires_grad)
            elif isinstance(obj, tuple):
                return tuple(convert_dtype(o, dtype, requires_grad) for o in obj)
            else:
                return obj

        if not TEST_CUDA or not self.should_test_cuda:
            raise unittest.SkipTest('Excluded from CUDA tests')

        with set_default_dtype(self.default_dtype):
            cpu_input = self._get_input()
            cpu_target = self._get_target()
            cpu_module = self.constructor(*self.constructor_args)
            gpu_module = self.constructor(*self.constructor_args)

            # Convert input, target and module parameters to dtype
            cpu_input = convert_dtype(cpu_input, dtype, True)
            if cpu_target.is_floating_point() or cpu_target.is_complex():
                cpu_target = convert_dtype(cpu_target, dtype)
            cpu_module.type(dtype)
            gpu_module.type(dtype)

            # GPU setup
            gpu_input = to_gpu(cpu_input)
            gpu_target = to_gpu(cpu_target)
            gpu_module.cuda()

            # torch.HalfTensor doesn't support most operations, converting back to default
            if dtype in {torch.half, torch.bfloat16}:
                cpu_input = self._get_input()
                cpu_target = self._get_target()
                # Loss modules with weights require consistent input/module weight types
                cpu_module = self.constructor(*self.constructor_args)

            cpu_output = test_case._forward_criterion(cpu_module, cpu_input, cpu_target, extra_args=extra_args)
            gpu_output = test_case._forward_criterion(gpu_module, gpu_input, gpu_target, extra_args=extra_args)
            # dtype used to be able to be None, so set precision in this way instead of a precision map
            test_case.assertEqual(cpu_output, gpu_output,
                                  atol=1e-1 if dtype in {torch.half, torch.bfloat16} else 4e-4, rtol=0, exact_dtype=False)

            cpu_gradInput = test_case._backward_criterion(
                cpu_module, cpu_input, cpu_output, cpu_target, extra_args=extra_args)
            gpu_gradInput = test_case._backward_criterion(
                gpu_module, gpu_input, gpu_output, gpu_target, extra_args=extra_args)
            # dtype used to be able to be None, so set precision in this way instead of a precision map
            test_case.assertEqual(cpu_gradInput, gpu_gradInput,
                                  atol=1e-1 if dtype in {torch.half, torch.bfloat16} else 4e-4, rtol=0, exact_dtype=False)