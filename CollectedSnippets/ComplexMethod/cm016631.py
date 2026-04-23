def apply_model_with_memblocks(model, x, parallel, show_progress_bar):

    B, T, C, H, W = x.shape
    if parallel:
        x = x.reshape(B*T, C, H, W)
        # parallel over input timesteps, iterate over blocks
        for b in tqdm(model, disable=not show_progress_bar):
            if isinstance(b, MemBlock):
                BT, C, H, W = x.shape
                T = BT // B
                _x = x.reshape(B, T, C, H, W)
                mem = F.pad(_x, (0,0,0,0,0,0,1,0), value=0)[:,:T].reshape(x.shape)
                x = b(x, mem)
            else:
                x = b(x)
        BT, C, H, W = x.shape
        T = BT // B
        x = x.view(B, T, C, H, W)
    else:
        out = []
        work_queue = deque([TWorkItem(xt, 0) for t, xt in enumerate(x.reshape(B, T * C, H, W).chunk(T, dim=1))])
        progress_bar = tqdm(range(T), disable=not show_progress_bar)
        mem = [None] * len(model)
        while work_queue:
            xt, i = work_queue.popleft()
            if i == 0:
                progress_bar.update(1)
            if i == len(model):
                out.append(xt)
                del xt
            else:
                b = model[i]
                if isinstance(b, MemBlock):
                    if mem[i] is None:
                        xt_new = b(xt, xt * 0)
                        mem[i] = xt.detach().clone()
                    else:
                        xt_new = b(xt, mem[i])
                        mem[i] = xt.detach().clone()
                    del xt
                    work_queue.appendleft(TWorkItem(xt_new, i+1))
                elif isinstance(b, TPool):
                    if mem[i] is None:
                        mem[i] = []
                    mem[i].append(xt.detach().clone())
                    if len(mem[i]) == b.stride:
                        B, C, H, W = xt.shape
                        xt = b(torch.cat(mem[i], 1).view(B*b.stride, C, H, W))
                        mem[i] = []
                        work_queue.appendleft(TWorkItem(xt, i+1))
                elif isinstance(b, TGrow):
                    xt = b(xt)
                    NT, C, H, W = xt.shape
                    for xt_next in reversed(xt.view(B, b.stride*C, H, W).chunk(b.stride, 1)):
                        work_queue.appendleft(TWorkItem(xt_next, i+1))
                    del xt
                else:
                    xt = b(xt)
                    work_queue.appendleft(TWorkItem(xt, i+1))
        progress_bar.close()
        x = torch.stack(out, 1)
    return x