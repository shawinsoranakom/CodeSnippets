def padding_and_split_data(data, device_mesh=None):
    if device_mesh is not None:
        cp_size = device_mesh["cp"].size()
        cp_rank = device_mesh["cp"].get_local_rank()
        cp_group = device_mesh["cp"].get_group()
        for k, v in data.items():
            if isinstance(v, torch.Tensor) and v.ndim > 1:
                data_len = torch.tensor(v.shape[-1], device=v.device, dtype=torch.int64)
                global_data_len = [torch.empty_like(data_len) for _ in range(cp_size)]
                dist.all_gather(global_data_len, data_len, group=cp_group)
                max_data_len = max(global_data_len)
                pad_size = max_data_len - v.shape[-1] + (cp_size - max_data_len % cp_size) % cp_size
                if k == "labels":
                    pad_value = -100
                elif k == "loss_weights":
                    pad_value = 0.0
                else:
                    pad_value = 0
                pad_data = F.pad(v, (0, pad_size), value=pad_value)
                data[k] = torch.chunk(pad_data, chunks=cp_size, dim=-1)[cp_rank].contiguous()
    return data