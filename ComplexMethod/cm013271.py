def _test_send_recv_any_source(self, profiler_ctx):
            rank = dist.get_rank()
            send_recv_size = 10
            tensor = _build_tensor(send_recv_size, value=rank)
            recv_ranks = []
            irecv_ranks = []

            ctx = profiler_ctx if profiler_ctx is not None else nullcontext()
            with ctx as prof:
                for dst in range(dist.get_world_size()):
                    if dst == rank:
                        # Recv mode
                        for dst in range(dist.get_world_size()):
                            if dst == rank:
                                continue

                            for recv in ["recv", "irecv"]:
                                output_tensor = _build_tensor(send_recv_size, value=-1)

                                if recv == "recv":
                                    sender = dist.recv(output_tensor)
                                    recv_ranks.append(sender)
                                elif recv == "irecv":
                                    work = dist.irecv(output_tensor)
                                    work.wait()
                                    sender = work._source_rank()
                                    irecv_ranks.append(sender)

                                # Assert the scalar value "sender" that should be
                                # equal to the rank of the sender is equal to all
                                # values in the received tensor.
                                self.assertTrue(output_tensor.eq(sender).all())
                    else:
                        # Send mode
                        dist.send(tensor, dst)  # recv
                        dist.send(tensor, dst)  # irecv

            if profiler_ctx is not None:
                backend = dist.get_backend()
                if backend in SEND_RECV_PROFILING_SUPPORTED_BACKENDS:
                    for event_name in [f"{backend}:send", f"{backend}:recvAnySource"]:
                        events = get_profiling_event(event_name, prof)
                        # Each rank sends/recvs from other rank twice.
                        self.assertEqual(
                            sum(event.count for event in events),
                            2 * (dist.get_world_size() - 1),
                        )
                        for event in events:
                            self.assertTrue(event.is_async)
                            self.assertEqual(event.input_shapes, [[send_recv_size] * 3])

                # Each rank would have 2 * (world_size - 1) sends, verify that
                # globally we receive the same amount on the other end.
                recv_ranks_tensor = torch.cat(
                    (torch.tensor(recv_ranks), torch.tensor(irecv_ranks)), 0
                )
                global_recv_ranks = [
                    torch.empty_like(recv_ranks_tensor)
                    for _ in range(dist.get_world_size())
                ]
                dist.all_gather(global_recv_ranks, recv_ranks_tensor)
                global_recv_ranks_list = []
                for tensor in global_recv_ranks:
                    global_recv_ranks_list += tensor.tolist()

                from itertools import groupby

                global_recv_ranks_list.sort()
                frequency = [
                    len(list(group)) for key, group in groupby(global_recv_ranks_list)
                ]
                self.assertEqual(dist.get_world_size(), len(frequency))
                self.assertEqual(
                    [2 * (dist.get_world_size() - 1)] * dist.get_world_size(), frequency
                )
                self._barrier()