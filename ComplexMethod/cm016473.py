def pin_memory(tensor):
    global TOTAL_PINNED_MEMORY
    if MAX_PINNED_MEMORY <= 0:
        return False

    if type(tensor).__name__ not in PINNING_ALLOWED_TYPES:
        return False

    if not is_device_cpu(tensor.device):
        return False

    if tensor.is_pinned():
        #NOTE: Cuda does detect when a tensor is already pinned and would
        #error below, but there are proven cases where this also queues an error
        #on the GPU async. So dont trust the CUDA API and guard here
        return False

    if not tensor.is_contiguous():
        return False

    size = tensor.nbytes
    if (TOTAL_PINNED_MEMORY + size) > MAX_PINNED_MEMORY:
        return False

    ptr = tensor.data_ptr()
    if ptr == 0:
        return False

    if torch.cuda.cudart().cudaHostRegister(ptr, size, 1) == 0:
        PINNED_MEMORY[ptr] = size
        TOTAL_PINNED_MEMORY += size
        return True
    else:
        logging.warning("Pin error.")
        discard_cuda_async_error()

    return False