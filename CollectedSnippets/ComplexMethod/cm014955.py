def test_to(self, device, dtype, module_info, training, swap, set_grad):
        module_cls = module_info.module_cls
        devices = ['cpu']
        if torch.cuda.is_available() or torch.xpu.is_available():
            devices += [device_type]
        dtypes = module_info.dtypes
        module_inputs = module_info.module_inputs_func(module_info, device=device, dtype=dtype,
                                                       requires_grad=False, training=training)
        torch.__future__.set_swap_module_params_on_conversion(swap)

        for module_input in module_inputs:
            c_args, c_kwargs = module_input.constructor_input.args, module_input.constructor_input.kwargs
            args, kwargs = module_input.forward_input.args, module_input.forward_input.kwargs

            m = module_cls(*c_args, **c_kwargs)

            # Avoid using `module.to()` when constructing module since that is the method we are testing
            def _to(m, set_grad=False):
                for c in m.children():
                    _to(c, set_grad=set_grad)
                for n, p in m.named_parameters(recurse=False):
                    new_p = torch.nn.Parameter(p.detach().clone().to(device, dtype))
                    setattr(m, n, new_p)
                    if set_grad:
                        new_p.grad = torch.randn_like(new_p)
                for n, b in m.named_buffers(recurse=False):
                    new_b = b.detach().clone().to(device, dtype)
                    setattr(m, n, new_b)
            _to(m, set_grad=set_grad)

            # Check .to() can be run after forward and backward with swap
            has_params = len(list(m.parameters())) > 0
            if swap and not set_grad and has_params:
                out = m(*args, **kwargs)
                if isinstance(out, tuple):
                    out = out[0]
                out.sum().backward()
                m.to(dtype=torch.half)
                # reset
                m.to(dtype=torch.float32)

            prev_device, prev_dtype = device, dtype
            for device_, dtype_ in product(devices, dtypes):
                # if device/dtype do not change, grad.to(device, dtype) is a no-op so
                # swapping will not change ._cdata
                # parameters will be wrapped in an nn.Parameter before swapping
                # which will cause the ._cdata to change
                g_no_swap = device_ == prev_device and dtype_ == prev_dtype
                prev_device, prev_dtype = device_, dtype_

                p_ids_before = [id(p) for p in m.parameters()]
                p_cdatas_before = [p._cdata for p in m.parameters()]
                if set_grad:
                    g_ids_before = [id(p.grad) for p in m.parameters()]
                    g_cdatas_before = [p.grad._cdata for p in m.parameters()]

                m.to(device=device_, dtype=dtype_)

                self.assertTrue(all(isinstance(p, torch.nn.Parameter) for p in m.parameters()))
                self.assertTrue(all(p.device.type == device_ for p in m.parameters()))
                self.assertTrue(all(p.dtype == dtype_ for p in m.parameters()))
                p_ids_after = [id(p) for p in m.parameters()]
                p_cdatas_after = [p._cdata for p in m.parameters()]

                if set_grad:
                    self.assertTrue(all(p.grad.device.type == device_ for p in m.parameters()))
                    self.assertTrue(all(p.grad.dtype == dtype_ for p in m.parameters()))
                    g_ids_after = [id(p.grad) for p in m.parameters()]
                    g_cdatas_after = [p.grad._cdata for p in m.parameters()]

                if swap:
                    # id same, ._cdata differs --> swapped cdata of THPVariable
                    self.assertTrue(all(a == b for a, b in zip(p_ids_before, p_ids_after)))
                    self.assertTrue(all(a != b for a, b in zip(p_cdatas_before, p_cdatas_after)))
                    if set_grad:
                        self.assertTrue(
                            all(a == b if g_no_swap else a != b for a, b in zip(g_cdatas_before, g_cdatas_after)))
                else:
                    # id and _cdata remain the same --> .data setting
                    self.assertTrue(all(a == b for a, b in zip(p_cdatas_before, p_cdatas_after)))
                    self.assertTrue(all(a == b for a, b in zip(p_ids_before, p_ids_after)))
                    if set_grad:
                        self.assertTrue(all(a == b for a, b in zip(g_cdatas_before, g_cdatas_after)))
                        self.assertTrue(all(a == b for a, b in zip(g_ids_before, g_ids_after)))