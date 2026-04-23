def forward(ctx, target_gpus, *inputs):
        if not all(i.device.type != "cpu" for i in inputs):
            raise AssertionError("Broadcast function not implemented for CPU tensors")
        target_gpus = [_get_device_index(x, True) for x in target_gpus]
        ctx.target_gpus = target_gpus
        if len(inputs) == 0:
            return ()
        ctx.num_inputs = len(inputs)
        ctx.input_device = inputs[0].get_device()

        ctx.complex_mask = [inp.is_complex() for inp in inputs]

        outputs = comm.broadcast_coalesced(inputs, ctx.target_gpus)

        for device_outputs in outputs:
            for i, is_complex in enumerate(ctx.complex_mask):
                if is_complex:
                    device_outputs[i] = torch.view_as_complex(device_outputs[i])

        non_differentiables = []
        for idx, input_requires_grad in enumerate(ctx.needs_input_grad[1:]):
            if not input_requires_grad:
                non_differentiables.extend(output[idx] for output in outputs)
        ctx.mark_non_differentiable(*non_differentiables)
        return tuple(chain.from_iterable(outputs))