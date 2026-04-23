def test_memory_format(self, device, dtype, module_info, training):
        is_sm86or80 = device.startswith("cuda") and (torch.cuda.get_device_capability(0) == (8, 6)
                                                     or torch.cuda.get_device_capability(0) == (8, 0))
        # TODO tighten it to a specific module
        atol, rtol = (3e-3, 7e-3) if is_sm86or80 else (None, None)
        module_cls = module_info.module_cls
        module_inputs = module_info.module_inputs_func(module_info, device=device, dtype=dtype,
                                                       requires_grad=True, training=training)
        module_memformat_affects_out = module_info.module_memformat_affects_out

        def _get_mem_formats(channels_last=False, channels_last_3d=False):
            if channels_last:
                return ([torch.contiguous_format, torch.channels_last],
                        [torch.preserve_format, torch.contiguous_format, torch.channels_last])
            elif channels_last_3d:
                return ([torch.contiguous_format, torch.channels_last_3d],
                        [torch.preserve_format, torch.contiguous_format, torch.channels_last_3d])
            else:
                return ([torch.contiguous_format],
                        [torch.preserve_format, torch.contiguous_format])

        # Check that at least one Tensor input has dim == n
        def _check_dims(obj, n):
            if isinstance(obj, torch.Tensor):
                return obj.dim() == n
            elif isinstance(obj, (tuple, list)):
                return any(_check_dims(o, n) for o in obj)
            else:
                return False

        # Called after _check_dims, when we know that >= 1 tensor can be converted to mem_format
        def _to_mem_format(mem_format, obj):
            def inner_to_mem_format(obj):
                d = obj.dim()
                if ((mem_format == torch.channels_last and d != 4)
                   or (mem_format == torch.channels_last_3d and d != 5)):
                    return obj.detach().clone().requires_grad_(obj.requires_grad)
                return obj.clone().to(memory_format=mem_format).detach().requires_grad_(obj.requires_grad)

            return self._traverse_obj(obj, inner_to_mem_format)

        def _check_out_mem_format(output, input_mem_format, module_mem_format):
            def inner_check_out_mem_format(output):
                d = output.dim()
                if (d == 4 and ((input_mem_format == torch.channels_last)
                                or (module_mem_format == torch.channels_last and module_memformat_affects_out))):
                    self.assertTrue(output.numel() == 0 or output.is_contiguous(memory_format=torch.channels_last))
                elif (d == 5 and ((input_mem_format == torch.channels_last_3d)
                                  or (module_mem_format == torch.channels_last_3d and module_memformat_affects_out))):
                    self.assertTrue(output.numel() == 0 or output.is_contiguous(memory_format=torch.channels_last_3d))
                else:
                    self.assertTrue(output.is_contiguous())
            return self._traverse_obj(output, inner_check_out_mem_format)

        def _req_grad(t):
            return isinstance(t, torch.Tensor) and t.requires_grad

        for module_input in module_inputs:
            if module_input.forward_input is None:
                continue

            supports_channels_last = _check_dims(module_input.forward_input.args, 4)
            supports_channels_last_3d = _check_dims(module_input.forward_input.args, 5)
            input_mem_formats, module_mem_formats = _get_mem_formats(supports_channels_last, supports_channels_last_3d)

            with freeze_rng_state():
                # === Instantiate the module. ===
                args, kwargs = module_input.constructor_input.args, module_input.constructor_input.kwargs

                m = module_cls(*args, **kwargs)
                m.to(device).to(dtype)
                m.train(training)

                # === Get output in (contiguous, contiguous) configuration. ===
                args, kwargs = module_input.forward_input.args, module_input.forward_input.kwargs
                desired_outputs = m(*args, **kwargs)
                # === Do backward pass. ===
                ref_diff_outputs = tuple(t for t in torch.utils._pytree.tree_leaves(desired_outputs) if _req_grad(t))
                if training and len(ref_diff_outputs) > 0:
                    params = tuple(p for p in m.parameters())
                    ref_diff_inputs = tuple(
                        t
                        for t in torch.utils._pytree.tree_leaves((args, kwargs, params))
                        if _req_grad(t)
                    )
                    ref_grad_outputs = tuple(
                        torch.rand_like(t)
                        for t in ref_diff_outputs
                    )
                    ref_grad_inputs = torch.autograd.grad(
                        ref_diff_outputs,
                        ref_diff_inputs,
                        grad_outputs=ref_grad_outputs,
                    )

                for input_mem_format in input_mem_formats:
                    # === Change memformat of input. ===
                    d_args = _to_mem_format(input_mem_format, module_input.forward_input.args)
                    d_kwargs = _to_mem_format(input_mem_format, module_input.forward_input.kwargs)

                    # See https://github.com/pytorch/pytorch/issues/107861
                    # When inductor tests are turned on, the setting of requires_grad will be lost
                    for t1, t2 in zip(
                        torch.utils._pytree.tree_leaves(d_args),
                        torch.utils._pytree.tree_leaves(module_input.forward_input.args),
                    ):
                        t1.requires_grad_(t2.requires_grad)
                    for t1, t2 in zip(
                        torch.utils._pytree.tree_leaves(d_kwargs),
                        torch.utils._pytree.tree_leaves(module_input.forward_input.kwargs),
                    ):
                        t1.requires_grad_(t2.requires_grad)

                    module_input.forward_input.args = d_args
                    module_input.forward_input.kwargs = d_kwargs

                    for module_mem_format in module_mem_formats:
                        # === Change memformat of module ===
                        m.to(memory_format=module_mem_format)

                        # === Do forward pass. ===
                        args, kwargs = module_input.forward_input.args, module_input.forward_input.kwargs
                        outputs = m(*args, **kwargs)

                        # === Compare outputs to (contiguous, contiguous) output. ===
                        if input_mem_format != torch.contiguous_format or module_mem_format != torch.contiguous_format:
                            self.assertEqual(outputs, desired_outputs, rtol=rtol, atol=atol)

                        # === Check mem format of output. ===
                        _check_out_mem_format(outputs, input_mem_format, module_mem_format)

                        # === Do backward pass. ===
                        diff_outputs = tuple(t for t in torch.utils._pytree.tree_leaves(outputs) if _req_grad(t))
                        if training and len(diff_outputs) > 0:
                            params = tuple(p for p in m.parameters())
                            diff_inputs = tuple(
                                t
                                for t in torch.utils._pytree.tree_leaves((args, kwargs, params))
                                if _req_grad(t)
                            )
                            grad_outputs = tuple(
                                torch.empty_like(t1).copy_(t2)
                                for (t1, t2) in zip(diff_outputs, ref_grad_outputs)
                            )

                            grad_inputs = torch.autograd.grad(
                                diff_outputs,
                                diff_inputs,
                                grad_outputs=grad_outputs,
                            )

                            if (
                                input_mem_format != torch.contiguous_format
                                or module_mem_format != torch.contiguous_format
                            ):
                                self.assertEqual(
                                    grad_inputs, ref_grad_inputs, rtol=rtol, atol=atol
                                )

                            # === Check mem format of grad_inputs. ===
                            _check_out_mem_format(grad_inputs, input_mem_format, module_mem_format)