def to_map(obj):
        if isinstance(obj, (torch.Tensor, PackedSequence)):
            device = obj.data.device if isinstance(obj, PackedSequence) else obj.device
            if device == target_device:
                return (obj,)
            if not use_side_stream_for_tensor_copies:
                return (obj.to(target_device),)
            else:
                # If the custom module is not registered to torch, stream is not used for acceleration
                if device.type == "cpu":
                    return (obj.to(target_device),)

                from torch.nn.parallel._functions import _get_stream

                # Perform CPU -> target_device copies in a background stream. This code is
                # motivated from similar logic in torch/nn/parallel/_functions.py
                stream = _get_stream(target_device)
                with stream:
                    output = obj.to(target_device)
                # synchronize with the copy stream
                with torch.accelerator.device_index(target_device.index):
                    current_stream = torch.accelerator.current_stream()
                    # Sync the current stream with the copy stream
                    current_stream.wait_stream(stream)
                    # Ensure tensor memory is not reused until work on
                    # main stream is complete
                    if isinstance(obj, PackedSequence):
                        output.data.record_stream(current_stream)  # type: ignore[arg-type]
                    else:
                        if not isinstance(output, torch.Tensor):
                            raise AssertionError("output must be a torch.Tensor")
                        output.record_stream(current_stream)  # type: ignore[arg-type]
                return (output,)

        from torch.nn.parallel.scatter_gather import _is_namedtuple

        if _is_namedtuple(obj):
            # pyrefly: ignore [bad-argument-type, no-matching-overload]
            return [type(obj)(*args) for args in zip(*map(to_map, obj))]
        if isinstance(obj, tuple) and len(obj) > 0:
            # pyrefly: ignore [bad-argument-type, no-matching-overload]
            return list(zip(*map(to_map, obj)))
        if isinstance(obj, list) and len(obj) > 0:
            # pyrefly: ignore [bad-argument-type, no-matching-overload]
            return [list(i) for i in zip(*map(to_map, obj))]
        if isinstance(obj, dict) and len(obj) > 0:
            # pyrefly: ignore [bad-argument-type, no-matching-overload]
            return [type(obj)(i) for i in zip(*map(to_map, obj.items()))]
        return [obj]