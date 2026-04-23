def cast_to_gathered(tensors, r, non_blocking=False, stream=None):
    wf_context = nullcontext()
    if stream is not None:
       wf_context = stream
       if hasattr(wf_context, "as_context"):
           wf_context = wf_context.as_context(stream)

    dest_views = comfy.memory_management.interpret_gathered_like(tensors, r)
    with wf_context:
        for tensor in tensors:
            dest_view = dest_views.pop(0)
            if tensor is None:
                continue
            if comfy.memory_management.read_tensor_file_slice_into(tensor, dest_view):
                continue
            storage = tensor._qdata.untyped_storage() if isinstance(tensor, comfy.quant_ops.QuantizedTensor) else tensor.untyped_storage()
            if hasattr(storage, "_comfy_tensor_mmap_touched"):
                storage._comfy_tensor_mmap_touched = True
            dest_view.copy_(tensor, non_blocking=non_blocking)