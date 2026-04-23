def get_cast_buffer(offload_stream, device, size, ref):
    global LARGEST_CASTED_WEIGHT

    if offload_stream is not None:
        wf_context = offload_stream
        if hasattr(wf_context, "as_context"):
            wf_context = wf_context.as_context(offload_stream)
    else:
        wf_context = nullcontext()

    cast_buffer = STREAM_CAST_BUFFERS.get(offload_stream, None)
    if cast_buffer is None or cast_buffer.numel() < size:
        if ref is LARGEST_CASTED_WEIGHT[0]:
            #If there is one giant weight we do not want both streams to
            #allocate a buffer for it. It's up to the caster to get the other
            #offload stream in this corner case
            return None
        if cast_buffer is not None and cast_buffer.numel() > 50 * (1024 ** 2):
            #I want my wrongly sized 50MB+ of VRAM back from the caching allocator right now
            synchronize()
            del STREAM_CAST_BUFFERS[offload_stream]
            del cast_buffer
            soft_empty_cache()
        with wf_context:
            cast_buffer = torch.empty((size), dtype=torch.int8, device=device)
            STREAM_CAST_BUFFERS[offload_stream] = cast_buffer

        if  size > LARGEST_CASTED_WEIGHT[1]:
            LARGEST_CASTED_WEIGHT = (ref, size)

    return cast_buffer