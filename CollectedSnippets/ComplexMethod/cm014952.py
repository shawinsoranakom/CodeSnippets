def _test_gradients_helper(self, device, dtype, module_info, training, check):
        # Check gradients
        module_cls = module_info.module_cls
        module_inputs = module_info.module_inputs_func(module_info, device=device, dtype=dtype,
                                                       requires_grad=True, training=training)
        if "xpu" in device and module_info.name == "nn.MultiheadAttention":
            self.skipTest("GradcheckError issue in MultiheadAttention, https://github.com/intel/torch-xpu-ops/issues/2356")
        # === Set nondet tol for gradcheck to user-defined value if on CUDA and cudNN is enabled
        gradcheck_nondet_tol = 0.0
        if (torch.device(device).type == 'cuda' and torch.backends.cudnn.enabled) or device_type == "xpu":
            gradcheck_nondet_tol = module_info.gradcheck_nondet_tol

        for module_input in module_inputs:
            if module_input.forward_input is None:
                continue

            # === Instantiate the module. ===
            args, kwargs = module_input.constructor_input.args, module_input.constructor_input.kwargs
            m = module_cls(*args, **kwargs)
            m.to(device).to(dtype)
            m.train(training)

            params = tuple(m.parameters())

            # === Lazy modules need to see an input to initialize params before gradcheck is run. ===
            input_args, input_kwargs = module_input.forward_input.args, module_input.forward_input.kwargs
            if issubclass(module_info.module_cls, torch.nn.modules.lazy.LazyModuleMixin):
                with torch.no_grad():
                    m(*input_args, **input_kwargs)

            # === Perform gradient check on the input_args ===
            other_kwargs = {}
            kwarg_tensors = []
            for name, obj in input_kwargs.items():
                if isinstance(obj, torch.Tensor):
                    kwarg_tensors.append((name, obj))
                else:
                    other_kwargs[name] = obj

            def fn_to_gradcheck(*flat_input_and_params):
                input_and_params = torch.utils._pytree.tree_unflatten(flat_input_and_params, flat_spec)
                new_input_args = input_and_params[:len(input_args)]
                kwarg_args = input_and_params[-len(kwarg_tensors):]
                new_kwargs = {name: obj for (name, _), obj in zip(kwarg_tensors, kwarg_args)}

                with freeze_rng_state():
                    output = m(*new_input_args, **new_kwargs, **other_kwargs)
                    output_flattened = torch.utils._pytree.tree_leaves(output)
                    return output_flattened

            def do_check(flat_input):
                self.assertTrue(
                    check(
                        fn_to_gradcheck,
                        flat_input,
                        nondet_tol=gradcheck_nondet_tol,
                        fast_mode=module_info.gradcheck_fast_mode
                    ))

            # check total derivative
            grad_input = input_args + params + tuple(obj for (_, obj) in kwarg_tensors)
            flat_input, flat_spec = torch.utils._pytree.tree_flatten(grad_input)
            do_check(flat_input)

            # check partial derivatives
            old_params_requires_grad = [p.requires_grad for p in params]
            for p in params:
                p.requires_grad = False

            old_kwargs_requires_grad = [obj.requires_grad for (_, obj) in kwarg_tensors]
            for (_, obj) in kwarg_tensors:
                obj.requires_grad = False

            for p, old in zip(params, old_params_requires_grad):
                p.requires_grad = old
                grad_input = input_args + params + tuple(obj for (_, obj) in kwarg_tensors)
                flat_input, flat_spec = torch.utils._pytree.tree_flatten(grad_input)
                do_check(flat_input)
                p.requires_grad = False

            for (_, obj), old in zip(kwarg_tensors, old_kwargs_requires_grad):
                obj.requires_grad = old
                grad_input = input_args + params + tuple(obj for (_, obj) in kwarg_tensors)
                flat_input, flat_spec = torch.utils._pytree.tree_flatten(grad_input)
                do_check(flat_input)
                obj.requires_grad = False