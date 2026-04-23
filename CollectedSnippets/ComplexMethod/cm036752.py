def test_gpu_write(device):
    torch.set_default_device(device)
    cpu_tensor = torch.zeros(10, 10, device="cpu", pin_memory=True, dtype=torch.int32)
    cuda_view = get_accelerator_view_from_cpu_tensor(cpu_tensor)
    assert cuda_view.device.type == "cuda"

    assert cuda_view[0, 0] == 0
    assert cuda_view[2, 3] == 0
    assert cuda_view[4, 5] == 0

    cuda_view[0, 0] = 1
    cuda_view[2, 3] = 2
    cuda_view[4, 5] = -1
    cuda_view.mul_(2)

    assert cpu_tensor[0, 0] == 2
    assert cpu_tensor[2, 3] == 4
    assert cpu_tensor[4, 5] == -2