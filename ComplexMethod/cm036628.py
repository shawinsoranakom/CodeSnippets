def worker_fn():
    rank = dist.get_rank()
    if rank == 0:
        port = get_open_port()
        ip = "127.0.0.1"
        dist.broadcast_object_list([ip, port], src=0)
    else:
        recv = [None, None]
        dist.broadcast_object_list(recv, src=0)
        ip, port = recv  # type: ignore

    stateless_pg = StatelessProcessGroup.create(ip, port, rank, dist.get_world_size())

    for pg in [dist.group.WORLD, stateless_pg]:
        writer_rank = 2
        broadcaster = MessageQueue.create_from_process_group(
            pg, 40 * 1024, 2, writer_rank
        )
        if rank == writer_rank:
            seed = random.randint(0, 1000)
            dist.broadcast_object_list([seed], writer_rank)
        else:
            recv = [None]
            dist.broadcast_object_list(recv, writer_rank)
            seed = recv[0]  # type: ignore

        if pg == dist.group.WORLD:
            dist.barrier()
        else:
            pg.barrier()

        # in case we find a race condition
        # print the seed so that we can reproduce the error
        print(f"Rank {rank} got seed {seed}")
        # test broadcasting with about 400MB of data
        N = 10_000
        if rank == writer_rank:
            arrs = get_arrays(N, seed)
            for x in arrs:
                broadcaster.broadcast_object(x)
                time.sleep(random.random() / 1000)
        else:
            arrs = get_arrays(N, seed)
            for x in arrs:
                y = broadcaster.broadcast_object(None)
                assert np.array_equal(x, y)
                time.sleep(random.random() / 1000)

        if pg == dist.group.WORLD:
            dist.barrier()
            print(f"torch distributed passed the test! Rank {rank}")
        else:
            pg.barrier()
            print(f"StatelessProcessGroup passed the test! Rank {rank}")