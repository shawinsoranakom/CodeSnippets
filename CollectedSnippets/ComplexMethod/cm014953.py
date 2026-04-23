def test_cpu_gpu_parity(self, device, dtype, module_info, training):
        # TODO: RNN / GRU / LSTM don't support backwards on eval mode for cuDNN; skip this in a
        # nicer way for eval mode only.
        # See https://github.com/pytorch/pytorch/issues/79161
        rnn_modules = {torch.nn.RNN, torch.nn.GRU, torch.nn.LSTM}
        if (module_info.module_cls in rnn_modules
                and not training
                and 'cuda' in device
                and torch.backends.cudnn.enabled):
            return

        # Test cpu and gpu results are the same
        module_cls = module_info.module_cls
        module_inputs_cpu = module_info.module_inputs_func(module_info, device="cpu", dtype=dtype,
                                                           requires_grad=True, training=training)

        def _to_device(obj):
            if isinstance(obj, torch.Tensor):
                res = obj.detach().to(device=device)
                res.requires_grad = obj.requires_grad
                return res
            elif isinstance(obj, tuple):
                return tuple(_to_device(o) for o in obj)
            elif isinstance(obj, dict):
                return {key: _to_device(o) for key, o in obj.items()}
            else:
                return deepcopy(obj)

        for module_input in module_inputs_cpu:
            # === Move input from cpu to device ===
            cpu_forward_args = module_input.forward_input.args
            cpu_forward_kwargs = module_input.forward_input.kwargs

            gpu_forward_args, gpu_forward_kwargs = _to_device((cpu_forward_args, cpu_forward_kwargs))

            self._retain_grad((cpu_forward_args, cpu_forward_kwargs, gpu_forward_args, gpu_forward_kwargs))

            # === Construct module on cpu and gpu ===
            args, kwargs = module_input.constructor_input.args, module_input.constructor_input.kwargs

            cpu_module = module_cls(*args, **kwargs).to(dtype).to("cpu")
            cpu_module.train(training)
            gpu_module = module_cls(*args, **kwargs).to(dtype).to(device)
            gpu_module.train(training)

            # === Lazy modules need to see an input to initialize params ===
            if issubclass(module_cls, torch.nn.modules.lazy.LazyModuleMixin):
                with torch.no_grad():
                    cpu_module(*cpu_forward_args, **cpu_forward_kwargs)
                    gpu_module(*gpu_forward_args, **gpu_forward_kwargs)

            for cpu_p, gpu_p in zip(cpu_module.parameters(), gpu_module.parameters()):
                gpu_p.data.copy_(cpu_p)

            # === Compare forward output between cpu and gpu ===
            cpu_outputs = cpu_module(*cpu_forward_args, **cpu_forward_kwargs)
            gpu_outputs = gpu_module(*gpu_forward_args, **gpu_forward_kwargs)

            self.assertEqual(cpu_outputs, gpu_outputs)

            # === Run backwards on CPU and GPU and compare results ===
            def check_backward(cpu_output, gpu_output):
                cpu_grad_output = cpu_output.clone().normal_()
                gpu_grad_output = cpu_grad_output.type_as(gpu_output)

                cpu_output.backward(cpu_grad_output, retain_graph=True)
                gpu_output.backward(gpu_grad_output, retain_graph=True)

                cpu_grad_input = self._get_grads(cpu_forward_args)
                gpu_grad_input = self._get_grads(gpu_forward_args)
                self.assertEqual(cpu_grad_input, gpu_grad_input)

                for cpu_p, gpu_p in zip(cpu_module.parameters(), gpu_module.parameters()):
                    self.assertEqual(cpu_p.grad, gpu_p.grad)

                cpu_grad_kwarg_input = self._get_grads(cpu_forward_kwargs)
                gpu_grad_kwarg_input = self._get_grads(gpu_forward_kwargs)
                self.assertEqual(cpu_grad_kwarg_input, gpu_grad_kwarg_input)

            for _ in range(5):
                if isinstance(cpu_outputs, torch.Tensor):
                    check_backward(cpu_outputs, gpu_outputs)
                else:
                    flatten_cpu_outputs = torch.utils._pytree.tree_leaves(cpu_outputs)
                    flatten_gpu_outputs = torch.utils._pytree.tree_leaves(gpu_outputs)
                    for cpu_output, gpu_output in zip(flatten_cpu_outputs, flatten_gpu_outputs):
                        if cpu_output.requires_grad:
                            check_backward(cpu_output, gpu_output)