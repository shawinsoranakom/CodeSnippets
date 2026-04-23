def get_offload_stream(device):
    stream_counter = stream_counters.get(device, 0)
    if NUM_STREAMS == 0:
        return None

    if torch.compiler.is_compiling():
        return None

    if device in STREAMS:
        ss = STREAMS[device]
        #Sync the oldest stream in the queue with the current
        ss[stream_counter].wait_stream(current_stream(device))
        stream_counter = (stream_counter + 1) % len(ss)
        stream_counters[device] = stream_counter
        return ss[stream_counter]
    elif is_device_cuda(device):
        ss = []
        for k in range(NUM_STREAMS):
            s1 = torch.cuda.Stream(device=device, priority=0)
            s1.as_context = torch.cuda.stream
            ss.append(s1)
        STREAMS[device] = ss
        s = ss[stream_counter]
        stream_counters[device] = stream_counter
        return s
    elif is_device_xpu(device):
        ss = []
        for k in range(NUM_STREAMS):
            s1 = torch.xpu.Stream(device=device, priority=0)
            s1.as_context = torch.xpu.stream
            ss.append(s1)
        STREAMS[device] = ss
        s = ss[stream_counter]
        stream_counters[device] = stream_counter
        return s
    return None