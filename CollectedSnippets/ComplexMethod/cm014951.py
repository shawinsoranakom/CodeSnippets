def test_non_contiguous_tensors(self, device, dtype, module_info, training):
        # Check modules work with non-contiguous tensors

        module_cls = module_info.module_cls
        module_inputs = module_info.module_inputs_func(module_info, device=device, dtype=dtype,
                                                       requires_grad=True, training=training)

        def _make_non_contiguous(obj):
            def inner_make_non_contiguous(obj):
                # Scalar tensors can not be made non-contiguous
                if not isinstance(obj, torch.Tensor) or obj.dim() == 0:
                    return obj

                out = torch.repeat_interleave(obj, 2, dim=-1)
                out = out[..., ::2].detach()
                out.requires_grad = obj.requires_grad
                return out
            return self._traverse_obj(obj, inner_make_non_contiguous)

        def _can_be_noncontiguous(obj):
            if isinstance(obj, (tuple, list)):
                return any(_can_be_noncontiguous(o) for o in obj)
            elif isinstance(obj, dict):
                return any(_can_be_noncontiguous(o) for o in obj.values())
            # scalar tensors can not be non-contiguous
            return isinstance(obj, torch.Tensor) and obj.dim() != 0

        for module_input in module_inputs:
            if module_input.forward_input is None:
                continue

            input_args, input_kwargs = module_input.forward_input.args, module_input.forward_input.kwargs
            if not (_can_be_noncontiguous(input_args) or _can_be_noncontiguous(input_kwargs)):
                continue

            # === Instantiate the module. ===
            args, kwargs = module_input.constructor_input.args, module_input.constructor_input.kwargs
            m = module_cls(*args, **kwargs)
            m.to(device).to(dtype)
            m.train(training)

            self._retain_grad((input_args, input_kwargs))

            # === Forward with default input
            with freeze_rng_state():
                default_output = m(*input_args, **input_kwargs)
                if isinstance(default_output, torch.Tensor):
                    grad_output = default_output.clone().detach_().normal_()
                    default_output.backward(grad_output, retain_graph=True)
                else:
                    grad_output = tuple(self._traverse_obj(o, lambda o: o.clone().detach_().normal_() if o.requires_grad else None)
                                        for o in default_output)
                    flattened_default_output = torch.utils._pytree.tree_leaves(default_output)
                    flattened_grad_output = torch.utils._pytree.tree_leaves(grad_output)
                    for o, g_o in zip(flattened_default_output, flattened_grad_output):
                        if (o.requires_grad):
                            o.backward(g_o, retain_graph=True)

            default_input_args_grad, default_input_kwargs_grad = deepcopy(self._get_grads((input_args, input_kwargs)))
            default_param_grad = deepcopy([p.grad for p in m.parameters()])

            # === Construct non-contiguous tensors ===
            nc_input_args, nc_input_kwargs = _make_non_contiguous((input_args, input_kwargs))
            nc_grad_output = _make_non_contiguous(grad_output)

            # === Compare results with non-contiguous and contiguous tensors ===
            inputs = [(input_args, input_kwargs), (nc_input_args, nc_input_kwargs)]
            grads = [grad_output, nc_grad_output]

            for (in_args, in_kwargs), g_out in product(inputs, grads):
                g_out_copy = deepcopy(g_out)
                self._zero_grad((in_args, in_kwargs))
                self._zero_grad(m.parameters())

                with freeze_rng_state():
                    out = m(*in_args, **in_kwargs)
                    if isinstance(out, torch.Tensor):
                        out.backward(g_out_copy, retain_graph=True)
                    else:
                        flattened_out = torch.utils._pytree.tree_leaves(out)
                        flattened_g_out_copy = torch.utils._pytree.tree_leaves(g_out_copy)
                        for o, g_o in zip(flattened_out, flattened_g_out_copy):
                            if o.requires_grad:
                                o.backward(g_o, retain_graph=True)

                input_args_grad, input_kwargs_grad = self._get_grads((in_args, in_kwargs))
                self.assertEqual(out, default_output)
                self.assertEqual(input_args_grad, default_input_args_grad, atol=1e-4, rtol=0)
                self.assertEqual(input_kwargs_grad, default_input_kwargs_grad, atol=1e-4, rtol=0)

                param_grad = [p.grad for p in m.parameters()]
                self.assertEqual(param_grad, default_param_grad)