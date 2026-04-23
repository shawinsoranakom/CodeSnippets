def in_the_same_node_as(
    pg: ProcessGroup | StatelessProcessGroup, source_rank: int = 0
) -> list[bool]:
    """
    This is a collective operation that returns if each rank is in the same node
    as the source rank. It tests if processes are attached to the same
    memory system (shared access to shared memory).
    """
    if isinstance(pg, ProcessGroup):
        assert torch.distributed.get_backend(pg) != torch.distributed.Backend.NCCL, (
            "in_the_same_node_as should be tested with a non-NCCL group."
        )
        # local rank inside the group
        rank = torch.distributed.get_rank(group=pg)
        world_size = torch.distributed.get_world_size(group=pg)

        # global ranks of the processes in the group
        ranks = torch.distributed.get_process_group_ranks(pg)
    else:
        rank = pg.rank
        world_size = pg.world_size
        ranks = list(range(world_size))

    # local tensor in each process to store the result
    is_in_the_same_node = torch.tensor(
        [0] * world_size, dtype=torch.int32, device="cpu"
    )

    magic_message = b"magic_message"
    shm = None

    try:
        with contextlib.suppress(OSError):
            if rank == source_rank:
                # create a shared memory segment
                shm = shared_memory.SharedMemory(create=True, size=128)
                assert shm.buf is not None, "Buffer was not created"
                shm.buf[: len(magic_message)] = magic_message
                if isinstance(pg, ProcessGroup):
                    torch.distributed.broadcast_object_list(
                        [shm.name], src=ranks[source_rank], group=pg
                    )
                else:
                    pg.broadcast_obj(shm.name, src=source_rank)
                is_in_the_same_node[rank] = 1
            else:
                # try to open the shared memory segment
                if isinstance(pg, ProcessGroup):
                    recv = [None]
                    torch.distributed.broadcast_object_list(
                        recv, src=ranks[source_rank], group=pg
                    )
                    name = recv[0]
                else:
                    name = pg.broadcast_obj(None, src=source_rank)
                # fix to https://stackoverflow.com/q/62748654/9191338
                # Python incorrectly tracks shared memory even if it is not
                # created by the process. The following patch is a workaround.
                with patch(
                    "multiprocessing.resource_tracker.register",
                    lambda *args, **kwargs: None,
                ):
                    shm = shared_memory.SharedMemory(name=name)
                assert shm.buf is not None, "Buffer was not opened"
                if shm.buf[: len(magic_message)] == magic_message:
                    is_in_the_same_node[rank] = 1
    except Exception as e:
        logger.error("Error ignored in is_in_the_same_node: %s", e)
    finally:
        if shm:
            shm.close()

    if isinstance(pg, ProcessGroup):
        torch.distributed.barrier(group=pg)
    else:
        pg.barrier()

    # clean up the shared memory segment
    with contextlib.suppress(OSError):
        if rank == source_rank and shm:
            shm.unlink()

    if isinstance(pg, ProcessGroup):
        torch.distributed.all_reduce(is_in_the_same_node, group=pg)
        aggregated_data = is_in_the_same_node
    else:
        aggregated_data = torch.zeros_like(is_in_the_same_node)
        for i in range(world_size):
            rank_data = pg.broadcast_obj(is_in_the_same_node, src=i)
            aggregated_data += rank_data

    return [x == 1 for x in aggregated_data.tolist()]