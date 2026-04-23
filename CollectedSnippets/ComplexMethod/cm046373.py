def profile_ops(input, ops, n=10, device=None, max_num_obj=0):
    """Ultralytics speed, memory and FLOPs profiler.

    Args:
        input (torch.Tensor | list): Input tensor(s) to profile.
        ops (nn.Module | list): Model or list of operations to profile.
        n (int, optional): Number of iterations to average.
        device (str | torch.device, optional): Device to profile on.
        max_num_obj (int, optional): Maximum number of objects for simulation.

    Returns:
        (list): Profile results for each operation.

    Examples:
        >>> from ultralytics.utils.torch_utils import profile_ops
        >>> input = torch.randn(16, 3, 640, 640)
        >>> m1 = lambda x: x * torch.sigmoid(x)
        >>> m2 = nn.SiLU()
        >>> profile_ops(input, [m1, m2], n=100)  # profile over 100 iterations
    """
    try:
        import thop
    except ImportError:
        thop = None  # conda support without 'ultralytics-thop' installed

    results = []
    if not isinstance(device, torch.device):
        device = select_device(device)
    LOGGER.info(
        f"{'Params':>12s}{'GFLOPs':>12s}{'GPU_mem (GB)':>14s}{'forward (ms)':>14s}{'backward (ms)':>14s}"
        f"{'input':>24s}{'output':>24s}"
    )
    gc.collect()  # attempt to free unused memory
    torch.cuda.empty_cache()
    for x in input if isinstance(input, list) else [input]:
        x = x.to(device)
        x.requires_grad = True
        for m in ops if isinstance(ops, list) else [ops]:
            m = m.to(device) if hasattr(m, "to") else m  # device
            m = m.half() if hasattr(m, "half") and isinstance(x, torch.Tensor) and x.dtype is torch.float16 else m
            tf, tb, t = 0, 0, [0, 0, 0]  # dt forward, backward
            try:
                flops = thop.profile(deepcopy(m), inputs=[x], verbose=False)[0] / 1e9 * 2 if thop else 0  # GFLOPs
            except Exception:
                flops = 0

            try:
                mem = 0
                for _ in range(n):
                    with cuda_memory_usage(device) as cuda_info:
                        t[0] = time_sync()
                        y = m(x)
                        t[1] = time_sync()
                        try:
                            (sum(yi.sum() for yi in y) if isinstance(y, list) else y).sum().backward()
                            t[2] = time_sync()
                        except Exception:  # no backward method
                            # print(e)  # for debug
                            t[2] = float("nan")
                    mem += cuda_info["memory"] / 1e9  # (GB)
                    tf += (t[1] - t[0]) * 1000 / n  # ms per op forward
                    tb += (t[2] - t[1]) * 1000 / n  # ms per op backward
                    if max_num_obj:  # simulate training with predictions per image grid (for AutoBatch)
                        with cuda_memory_usage(device) as cuda_info:
                            torch.randn(
                                x.shape[0],
                                max_num_obj,
                                int(sum((x.shape[-1] / s) * (x.shape[-2] / s) for s in m.stride.tolist())),
                                device=device,
                                dtype=torch.float32,
                            )
                        mem += cuda_info["memory"] / 1e9  # (GB)
                s_in, s_out = (tuple(x.shape) if isinstance(x, torch.Tensor) else "list" for x in (x, y))  # shapes
                p = sum(x.numel() for x in m.parameters()) if isinstance(m, nn.Module) else 0  # parameters
                LOGGER.info(f"{p:12}{flops:12.4g}{mem:>14.3f}{tf:14.4g}{tb:14.4g}{s_in!s:>24s}{s_out!s:>24s}")
                results.append([p, flops, mem, tf, tb, s_in, s_out])
            except Exception as e:
                LOGGER.info(e)
                results.append(None)
            finally:
                gc.collect()  # attempt to free unused memory
                torch.cuda.empty_cache()
    return results