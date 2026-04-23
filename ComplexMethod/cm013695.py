def _broadcast_coalesced_reshape(
    tensors: Sequence[torch.Tensor],
    devices: Sequence[int | torch.device],
    detach: bool = False,
) -> list[list[torch.Tensor]]:
    from torch.nn.parallel._functions import Broadcast

    if len(tensors) == 0:
        return []

    if detach:
        complex_mask = [
            not isinstance(t, torch.nn.UninitializedParameter) and t.is_complex()
            for t in tensors
        ]

        outputs = comm.broadcast_coalesced(tensors, devices)

        for device_outputs in outputs:
            for i, is_complex in enumerate(complex_mask):
                if is_complex:
                    device_outputs[i] = torch.view_as_complex(device_outputs[i])

        return outputs
    else:
        tensor_copies = Broadcast.apply(devices, *tensors)
        return [
            list(tensor_copies[i : i + len(tensors)])
            for i in range(0, len(tensor_copies), len(tensors))
        ]