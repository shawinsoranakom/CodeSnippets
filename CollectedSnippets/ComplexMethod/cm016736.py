def slice_attention(q, k, v):
    r1 = torch.zeros_like(k, device=q.device)
    scale = (int(q.shape[-1])**(-0.5))

    mem_free_total = model_management.get_free_memory(q.device)

    tensor_size = q.shape[0] * q.shape[1] * k.shape[2] * q.element_size()
    modifier = 3 if q.element_size() == 2 else 2.5
    mem_required = tensor_size * modifier
    steps = 1

    if mem_required > mem_free_total:
        steps = 2**(math.ceil(math.log(mem_required / mem_free_total, 2)))

    while True:
        try:
            slice_size = q.shape[1] // steps if (q.shape[1] % steps) == 0 else q.shape[1]
            for i in range(0, q.shape[1], slice_size):
                end = i + slice_size
                s1 = torch.bmm(q[:, i:end], k) * scale

                s2 = torch.nn.functional.softmax(s1, dim=2).permute(0,2,1)
                del s1

                r1[:, :, i:end] = torch.bmm(v, s2)
                del s2
            break
        except Exception as e:
            model_management.raise_non_oom(e)
            model_management.soft_empty_cache(True)
            steps *= 2
            if steps > 128:
                raise e
            logging.warning("out of memory error, increasing steps and trying again {}".format(steps))

    return r1