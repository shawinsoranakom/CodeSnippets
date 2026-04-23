def get_torch_device_name(device):
    if hasattr(device, 'type'):
        if device.type == "cuda":
            try:
                allocator_backend = torch.cuda.get_allocator_backend()
            except:
                allocator_backend = ""
            return "{} {} : {}".format(device, torch.cuda.get_device_name(device), allocator_backend)
        elif device.type == "xpu":
            return "{} {}".format(device, torch.xpu.get_device_name(device))
        else:
            return "{}".format(device.type)
    elif is_intel_xpu():
        return "{} {}".format(device, torch.xpu.get_device_name(device))
    elif is_ascend_npu():
        return "{} {}".format(device, torch.npu.get_device_name(device))
    elif is_mlu():
        return "{} {}".format(device, torch.mlu.get_device_name(device))
    else:
        return "CUDA {}: {}".format(device, torch.cuda.get_device_name(device))