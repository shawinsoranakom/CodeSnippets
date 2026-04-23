def get_total_memory(dev=None, torch_total_too=False):
    global directml_enabled
    if dev is None:
        dev = get_torch_device()

    if hasattr(dev, 'type') and (dev.type == 'cpu' or dev.type == 'mps'):
        mem_total = psutil.virtual_memory().total
        mem_total_torch = mem_total
    else:
        if directml_enabled:
            mem_total = 1024 * 1024 * 1024 #TODO
            mem_total_torch = mem_total
        elif is_intel_xpu():
            stats = torch.xpu.memory_stats(dev)
            mem_reserved = stats['reserved_bytes.all.current']
            mem_total_xpu = torch.xpu.get_device_properties(dev).total_memory
            mem_total_torch = mem_reserved
            mem_total = mem_total_xpu
        elif is_ascend_npu():
            stats = torch.npu.memory_stats(dev)
            mem_reserved = stats['reserved_bytes.all.current']
            _, mem_total_npu = torch.npu.mem_get_info(dev)
            mem_total_torch = mem_reserved
            mem_total = mem_total_npu
        elif is_mlu():
            stats = torch.mlu.memory_stats(dev)
            mem_reserved = stats['reserved_bytes.all.current']
            _, mem_total_mlu = torch.mlu.mem_get_info(dev)
            mem_total_torch = mem_reserved
            mem_total = mem_total_mlu
        else:
            stats = torch.cuda.memory_stats(dev)
            mem_reserved = stats['reserved_bytes.all.current']
            _, mem_total_cuda = torch.cuda.mem_get_info(dev)
            mem_total_torch = mem_reserved
            mem_total = mem_total_cuda

    if torch_total_too:
        return (mem_total, mem_total_torch)
    else:
        return mem_total