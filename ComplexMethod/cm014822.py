def test_module(self, device, dtype, module_info, training):
        class RNNWrapper(torch.nn.Module):
            def __init__(self, m_cons, args, kwargs):
                super().__init__()
                self.m = m_cons(*args, **kwargs)

            def forward(self, *inps):
                ret = self.m(*inps)
                if not isinstance(ret, tuple):
                    raise AssertionError(f"expected tuple, got {type(ret)}")
                return ret[0]

        def batch_hidden(h):
            new_h_shape = [1] * (len(h.shape) + 1)
            new_h_shape[1] = 2
            return h.unsqueeze(1).repeat(new_h_shape)

        module_cls = module_info.module_cls
        atol, rtol = (1e-3, 1e-4) if dtype == torch.float32 else (None, None)
        module_inputs = module_info.module_inputs_func(
            module_info,
            device=device,
            dtype=dtype,
            requires_grad=True,
            training=training,
            with_packed_sequence=True,
        )
        for module_input in module_inputs:
            if module_input.forward_input is None:
                continue
            args, kwargs = (
                module_input.constructor_input.args,
                module_input.constructor_input.kwargs,
            )
            m = RNNWrapper(module_cls, args, kwargs)
            batch_first = m.m.batch_first
            m.to(device).to(dtype)

            args, kwargs = (
                module_input.forward_input.args,
                module_input.forward_input.kwargs,
            )

            # if the RNN tests use unbatched inputs--batch the inputs
            input = args[0]
            if isinstance(input, torch.Tensor) and input.dim() == 2:
                input = input.detach()
                new_input_shape = [1] * (len(input.shape) + 1)
                if batch_first:
                    new_input_shape[0] = 2
                    input = input.repeat(new_input_shape)
                else:
                    new_input_shape[1] = 2
                    input = input.unsqueeze(1).repeat(new_input_shape)

                h = args[1] if len(args) > 1 else None
                if h is not None:
                    h = (
                        batch_hidden(h)
                        if isinstance(h, torch.Tensor)
                        else tuple(batch_hidden(hx) for hx in h)
                    )
                    args = list(args)
                    args[1] = h

            if isinstance(input, torch.nn.utils.rnn.PackedSequence):
                self._do_test_rnn_packed_sequence(
                    m, input, args[1:], kwargs, atol=atol, rtol=rtol
                )
            else:
                self._do_test(
                    m,
                    input,
                    args[1:],
                    kwargs,
                    batch_first=batch_first,
                    atol=atol,
                    rtol=rtol,
                )