def forward(ctx, target_device, dim, *inputs):
        if not all(i.device.type != "cpu" for i in inputs):
            raise AssertionError("Gather function not implemented for CPU tensors")
        if target_device == "cpu":
            ctx.target_device = "cpu"
        else:
            target_device = _get_device_index(target_device, True)
            ctx.target_device = target_device
        ctx.dim = dim
        ctx.input_gpus = tuple(i.get_device() for i in inputs)
        if all(t.dim() == 0 for t in inputs) and dim == 0:
            inputs = tuple(t.view(1) for t in inputs)
            warnings.warn(
                "Was asked to gather along dimension 0, but all "
                "input tensors were scalars; will instead unsqueeze "
                "and return a vector.",
                stacklevel=2,
            )
            ctx.unsqueezed_scalar = True
        else:
            ctx.unsqueezed_scalar = False
        ctx.input_sizes = tuple(i.size(ctx.dim) for i in inputs)

        is_complex = len(inputs) > 0 and inputs[0].is_complex()

        output = comm.gather(inputs, ctx.dim, ctx.target_device)

        if is_complex:
            output = torch.view_as_complex(output)

        return output