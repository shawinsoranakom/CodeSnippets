def create_from_process_group(
        pg: ProcessGroup | StatelessProcessGroup,
        max_chunk_bytes,
        max_chunks,
        writer_rank: int = 0,
        external_writer_handle=None,
        blocking: bool = True,
    ) -> "MessageQueue":
        """
        Creates a MessageQueue for a distributed process group with one writer and
        multiple readers.

        This method is designed for scenarios where one process (the writer) sends
        messages, and all other processes (the readers) receive messages. It sets up
        the shared memory buffer and socket communication handles accordingly, and
        broadcasts the handle from the writer to all readers.

        Args:
            pg (ProcessGroup | StatelessProcessGroup): The torch distributed process
                group.
            max_chunk_bytes (int): Maximum size in bytes for each chunk in the buffer.
            max_chunks (int): Maximum number of chunks in the buffer.
            writer_rank (int, optional): The global rank that will act as the writer.
                Defaults to 0.
            external_writer_handle (Handle, optional): Used when there is a handle
                from an external Message Queue. If provided, use this handle to init
                PG writer message queue instead of creating a new one. Defaults to None.
            blocking (bool, optional): If True, blocks until all processes are ready.
                Defaults to True.

        Returns:
            MessageQueue: The MessageQueue instance for the calling process.

        """
        if isinstance(pg, ProcessGroup):
            group_rank = dist.get_rank(pg)
            group_world_size = dist.get_world_size(pg)
            global_ranks = dist.get_process_group_ranks(pg)
        else:
            group_rank = pg.rank
            group_world_size = pg.world_size
            global_ranks = list(range(pg.world_size))
        from vllm.distributed.parallel_state import in_the_same_node_as

        status = in_the_same_node_as(pg, source_rank=writer_rank)
        if group_rank == writer_rank:
            if external_writer_handle is not None:
                buffer_io = MessageQueue.create_from_handle(
                    external_writer_handle, group_rank
                )
            else:
                same_node_ranks = [i for i, s in enumerate(status) if s]
                n_reader = group_world_size - 1
                n_local_reader = len(same_node_ranks) - 1
                local_reader_ranks = [i for i in same_node_ranks if i != writer_rank]
                buffer_io = MessageQueue(
                    n_reader=n_reader,
                    n_local_reader=n_local_reader,
                    local_reader_ranks=local_reader_ranks,
                    max_chunk_bytes=max_chunk_bytes,
                    max_chunks=max_chunks,
                )
            handle = buffer_io.export_handle()
            if isinstance(pg, ProcessGroup):
                dist.broadcast_object_list(
                    [handle], src=global_ranks[writer_rank], group=pg
                )
            else:
                pg.broadcast_obj(handle, writer_rank)
        else:
            if isinstance(pg, ProcessGroup):
                recv = [None]
                dist.broadcast_object_list(
                    recv, src=global_ranks[writer_rank], group=pg
                )
                handle = recv[0]  # type: ignore
            else:
                handle = pg.broadcast_obj(None, writer_rank)
            buffer_io = MessageQueue.create_from_handle(handle, group_rank)
        if blocking:
            buffer_io.wait_until_ready()
        return buffer_io