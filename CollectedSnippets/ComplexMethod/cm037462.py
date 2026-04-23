async def run_engine_stats_update_task():
            with (
                make_zmq_socket(self.ctx, stats_addr, zmq.XSUB, linger=0) as socket,
                make_zmq_socket(
                    self.ctx, self.first_req_sock_addr, zmq.PAIR, bind=False, linger=0
                ) as first_req_rcv_socket,
            ):
                assert isinstance(socket, zmq.asyncio.Socket)
                assert isinstance(first_req_rcv_socket, zmq.asyncio.Socket)
                self.resources.stats_update_socket = socket
                self.resources.first_req_rcv_socket = first_req_rcv_socket
                # Send subscription message.
                await socket.send(b"\x01")

                poller = zmq.asyncio.Poller()
                poller.register(socket, zmq.POLLIN)
                poller.register(first_req_rcv_socket, zmq.POLLIN)

                while True:
                    events = await poller.poll()
                    if (
                        not self.engines_running
                        and len(events) == 2
                        or (events[0][0] == first_req_rcv_socket)
                    ):
                        # Check if this is a regular request notification or
                        # scale up notification
                        buf = first_req_rcv_socket.recv(flags=zmq.NOBLOCK).result()

                        decoded = msgspec.msgpack.decode(buf)
                        if (
                            isinstance(decoded, (list, tuple))
                            and len(decoded) == 2
                            and decoded[0] == "SCALE_ELASTIC_EP"
                        ):
                            # Extract new engine count from the decoded message
                            new_engine_count = decoded[1]
                            # Update engine_ranks_managed and count_slice
                            parallel_config = self.vllm_config.parallel_config
                            dp_size = parallel_config.data_parallel_size
                            dp_rank = parallel_config.data_parallel_rank
                            assert dp_rank == 0
                            assert dp_size == new_engine_count
                            assert not (
                                parallel_config.data_parallel_hybrid_lb
                                or parallel_config.data_parallel_external_lb
                            )
                            num_ranks = dp_size
                            self.engine_ranks_managed = list(
                                range(dp_rank, dp_rank + num_ranks)
                            )
                            if len(self.lb_engines) < new_engine_count:
                                self.lb_engines = self.lb_engines + [
                                    [0, 0]
                                    for _ in range(
                                        new_engine_count - len(self.lb_engines)
                                    )
                                ]
                            else:
                                self.lb_engines = self.lb_engines[:new_engine_count]
                            # Send scale up notification to coordinator
                            scale_msg = msgspec.msgpack.encode(
                                ("SCALE_ELASTIC_EP", new_engine_count)
                            )
                            await socket.send(scale_msg)
                            continue

                        # we're sending a request while the engines are
                        # paused, so that it can wake the others up
                        # (to run dummy EP loop).
                        assert decoded[0] == "FIRST_REQ"
                        target_eng_index = decoded[1]
                        self.engines_running = True
                        msg = msgspec.msgpack.encode(
                            (target_eng_index, self.current_wave)
                        )
                        await socket.send(msg)

                    buf = None
                    while True:
                        # Drain all stats events (we only care about latest).
                        future: asyncio.Future[bytes] = socket.recv(flags=zmq.NOBLOCK)
                        if isinstance(future.exception(), zmq.Again):
                            break
                        buf = future.result()
                    if buf is None:
                        continue

                    # Update local load-balancing state.
                    counts, wave, running = msgspec.msgpack.decode(buf)
                    self.current_wave = wave
                    self.engines_running = running
                    if counts is not None:
                        # Running and waiting counts are global from the
                        # Coordinator including all EngineCores. Slice to get
                        # just the cores managed by this client.
                        ranks = self.engine_ranks_managed
                        count_slice = slice(ranks[0], ranks[-1] + 1)
                        sliced_counts = counts[count_slice]
                        self.lb_engines = sliced_counts
                        logger.debug(
                            "Received counts: %s (%s)", sliced_counts, count_slice
                        )