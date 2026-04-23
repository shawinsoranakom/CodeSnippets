def _do_test(self, test_case, module, input):
        num_threads = torch.get_num_threads()
        torch.set_num_threads(1)
        input_tuple = input if isinstance(input, tuple) else (input,)

        self._check_gradients(test_case, module, input_tuple)

        # check if module can be printed
        module.__repr__()

        if self.check_inplace:
            # check if the inplace variant of the module gives the same result
            # as the out-of-place

            # check_inplace doesn't support multiple input tensors, since we don't have any modules
            # that modify the inputs in-place and that accept more than one input
            if len(input_tuple) != 1:
                raise AssertionError(f"Expected len(input_tuple) == 1, got {len(input_tuple)}")
            input = input_tuple[0]

            module_ip = self.constructor(*self.constructor_args, inplace=True)

            input_version = input._version
            with freeze_rng_state():
                output = module(input)
            test_case.assertEqual(input._version, input_version)

            input_ip = deepcopy(input)
            input_ip_clone = input_ip.clone()
            with freeze_rng_state():
                output_ip = module_ip(input_ip_clone)
            test_case.assertNotEqual(input_ip_clone._version, input_version)
            test_case.assertEqual(output, output_ip)
            grad = output.data.clone().normal_()
            if input.grad is not None:
                with torch.no_grad():
                    input.grad.zero_()
            if input_ip.grad is not None:
                with torch.no_grad():
                    input_ip.grad.zero_()
            output.backward(grad)
            output_ip.backward(grad)
            test_case.assertEqual(input.grad, input_ip.grad)

        def assert_module_parameters_are(tensor_type, device_id=None):
            for p in module.parameters():
                test_case.assertIsInstance(p, tensor_type)
                if device_id is not None:
                    test_case.assertEqual(p.get_device(), device_id)

        if all(isinstance(t, torch.LongTensor) for t in input_tuple) and TEST_CUDA:
            # check that cuda() moves module parameters to correct GPU device,
            # and that float() casts parameters correctly
            input_tuple = tuple(t.cuda() for t in input_tuple)
            module.float().cuda()
            module(*input_tuple)
            assert_module_parameters_are(torch.cuda.FloatTensor, 0)  # type: ignore[attr-defined]

            if torch.cuda.device_count() > 1:
                input_tuple = tuple(t.cuda(1) for t in input_tuple)
                module.cuda(1)
                with torch.cuda.device(1):
                    module(*input_tuple)
                assert_module_parameters_are(torch.cuda.FloatTensor, 1)  # type: ignore[attr-defined]
        else:
            # check that float()/double() casters work correctly
            def to_type(tensor, real, complex):
                if tensor.is_complex():
                    return tensor.to(complex)
                elif tensor.is_floating_point():
                    return tensor.to(real)
                else:
                    return tensor

            def to_half(x):
                # TODO: torch.complex32 when properly supported
                return to_type(x, torch.float16, None)

            def to_single(x):
                return to_type(x, torch.float32, torch.complex64)

            def to_double(x):
                return to_type(x, torch.float64, torch.complex128)

            # to float
            input_tuple = tuple(to_single(t) for t in input_tuple)
            module.float()
            module(*input_tuple)
            assert_module_parameters_are(torch.FloatTensor)

            # and back to double
            input_tuple = tuple(to_double(t) for t in input_tuple)
            module.double()
            module(*input_tuple)
            assert_module_parameters_are(torch.DoubleTensor)

            if TEST_CUDA and self.should_test_cuda:
                # check that cuda() moves module parameters to correct GPU device,
                # and that float() casts parameters correctly

                # to GPU0
                input_tuple = tuple(to_single(t).cuda() for t in input_tuple)
                module.float().cuda()
                module(*input_tuple)
                assert_module_parameters_are(torch.cuda.FloatTensor, 0)  # type: ignore[attr-defined]

                # to CPU
                input_tuple = tuple(t.cpu() for t in input_tuple)
                module.cpu()
                module(*input_tuple)
                assert_module_parameters_are(torch.FloatTensor)

                # back to GPU0
                input_tuple = tuple(t.cuda() for t in input_tuple)
                module.cuda()
                module(*input_tuple)
                assert_module_parameters_are(torch.cuda.FloatTensor, 0)  # type: ignore[attr-defined]

                # test that forwards of module runs correctly without cuDNN
                if self.cudnn:
                    with torch.backends.cudnn.flags(enabled=False):
                        module(*input_tuple)
                        assert_module_parameters_are(torch.cuda.FloatTensor, 0)  # type: ignore[attr-defined]

                if torch.cuda.device_count() >= 2:
                    # test cross-GPU transfer works
                    # to GPU1
                    input_tuple = tuple(t.cuda(1) for t in input_tuple)
                    module.cuda(1)
                    with torch.cuda.device(1):
                        module(*input_tuple)
                    assert_module_parameters_are(torch.cuda.FloatTensor, 1)  # type: ignore[attr-defined]

                if not self.skip_double:
                    # test double()
                    input_tuple = tuple(to_double(t).cuda() for t in input_tuple)
                    module.double().cuda()
                    module(*input_tuple)
                    assert_module_parameters_are(torch.cuda.DoubleTensor, 0)  # type: ignore[attr-defined]

                # test half()
                if not self.skip_half:
                    input_tuple = tuple(to_half(t).cuda() for t in input_tuple)
                    module.half().cuda()
                    module(*input_tuple)
                    assert_module_parameters_are(torch.cuda.HalfTensor, 0)  # type: ignore[attr-defined]
        torch.set_num_threads(num_threads)