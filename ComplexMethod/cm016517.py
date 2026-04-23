def read_tensor_file_slice_into(tensor, destination):

    if isinstance(tensor, QuantizedTensor):
        if not isinstance(destination, QuantizedTensor):
            return False
        if tensor._layout_cls != destination._layout_cls:
            return False

        if not read_tensor_file_slice_into(tensor._qdata, destination._qdata):
            return False

        dst_orig_dtype = destination._params.orig_dtype
        destination._params.copy_from(tensor._params, non_blocking=False)
        destination._params = dataclasses.replace(destination._params, orig_dtype=dst_orig_dtype)
        return True

    info = getattr(tensor.untyped_storage(), "_comfy_tensor_file_slice", None)
    if info is None:
        return False

    file_obj = info.file_ref
    if (destination.device.type != "cpu"
            or file_obj is None
            or threading.get_ident() != info.thread_id
            or destination.numel() * destination.element_size() < info.size
            or tensor.numel() * tensor.element_size() != info.size
            or tensor.storage_offset() != 0
            or not tensor.is_contiguous()):
        return False

    if info.size == 0:
        return True

    buf_type = ctypes.c_ubyte * info.size
    view = memoryview(buf_type.from_address(destination.data_ptr()))

    try:
        file_obj.seek(info.offset)
        done = 0
        while done < info.size:
            try:
                n = file_obj.readinto(view[done:])
            except OSError:
                return False
            if n <= 0:
                return False
            done += n
        return True
    finally:
        view.release()