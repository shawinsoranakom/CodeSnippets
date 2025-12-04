def run(backend):
    tensor = torch.zeros(1)
    if backend == "nccl":
        device = torch.device(f"cuda:{LOCAL_RANK}")
        tensor = tensor.to(device)

    if WORLD_RANK == 0:
        for rank_recv in range(1, WORLD_SIZE):
            dist.send(tensor=tensor, dst=rank_recv)
            print(f"worker_{0} sent data to Rank {rank_recv}\n")
    else:
        dist.recv(tensor=tensor, src=0)
        print(f"worker_{WORLD_RANK} has received data from rank {0}\n")


def init_processes(backend):
    dist.init_process_group(backend, rank=WORLD_RANK, world_size=WORLD_SIZE)
    run(backend)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--local_rank", type=int, help="Local rank. Necessary for using the torch.distributed.launch utility."
    )
    parser.add_argument("--backend", type=str, default="nccl", choices=["nccl", "gloo"])
    args = parser.parse_args()

    init_processes(backend=args.backend)
