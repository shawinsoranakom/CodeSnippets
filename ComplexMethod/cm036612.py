def multiple_send_recv_worker_fn():
    device = torch.device(f"cuda:{torch.distributed.get_rank()}")
    groups = [
        torch.distributed.new_group(ranks=[0, 2], backend="gloo"),
        torch.distributed.new_group(ranks=[1, 3], backend="gloo"),
    ]
    group = groups[0] if torch.distributed.get_rank() in [0, 2] else groups[1]
    pynccl_comm = PyNcclCommunicator(group=group, device=device)
    if torch.distributed.get_rank() == 0:
        tensor = torch.ones(16, 1024, 1024, dtype=torch.float32, device=device)
    elif torch.distributed.get_rank() == 1:
        tensor = 2 * torch.ones(16, 1024, 1024, dtype=torch.float32, device=device)
    else:
        tensor = torch.empty(16, 1024, 1024, dtype=torch.float32, device=device)
    if torch.distributed.get_rank() in [0, 1]:
        pynccl_comm.send(tensor, dst=(pynccl_comm.rank + 1) % pynccl_comm.world_size)
    else:
        pynccl_comm.recv(tensor, src=(pynccl_comm.rank - 1) % pynccl_comm.world_size)
    torch.accelerator.synchronize()
    if torch.distributed.get_rank() in [0, 2]:
        assert torch.all(tensor == 1).cpu().item()
    else:
        assert torch.all(tensor == 2).cpu().item()