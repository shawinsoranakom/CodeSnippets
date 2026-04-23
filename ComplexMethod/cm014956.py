def test_to_empty(self, device, dtype, module_info, swap, training):
        module_cls = module_info.module_cls

        with torch.device("meta"):
            module_inputs = module_info.module_inputs_func(module_info, device=None, dtype=dtype,
                                                           requires_grad=False, training=training)

        torch.__future__.set_swap_module_params_on_conversion(swap)
        device_ = torch.device(device)

        for module_input in module_inputs:
            c_args, c_kwargs = module_input.constructor_input.args, module_input.constructor_input.kwargs

            with torch.device("meta"):
                m = module_cls(*c_args, **c_kwargs)

            p_ids_before = [id(p) for p in m.parameters()]
            p_cdatas_before = [p._cdata for p in m.parameters()]
            m.to_empty(device=device_)

            self.assertTrue(all(isinstance(p, torch.nn.Parameter) for p in m.parameters()))
            self.assertTrue(all(p.device == device_ for p in m.parameters()))
            self.assertTrue(all(p.dtype == dtype for p in m.parameters()))
            p_ids_after = [id(p) for p in m.parameters()]
            p_cdatas_after = [p._cdata for p in m.parameters()]

            if swap:
                # id same, ._cdata differs --> swapped cdata of THPVariable
                self.assertTrue(all(a == b for a, b in zip(p_ids_before, p_ids_after)))
                self.assertTrue(all(a != b for a, b in zip(p_cdatas_before, p_cdatas_after)))
            else:
                # id and ._cdata differ
                # meta and device have different shallow copy types, so this will create a new
                # parameter and assign it to the module
                self.assertTrue(all(a != b for a, b in zip(p_ids_before, p_ids_after)))
                self.assertTrue(all(a != b for a, b in zip(p_cdatas_before, p_cdatas_after)))