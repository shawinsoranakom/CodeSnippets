def next_rendezvous(self) -> RendezvousInfo:
        """See base class."""
        msg = (
            f"The node '{self._this_node}' attempts to join the next round of the rendezvous "
            f"'{self._settings.run_id}'."
        )
        self._record(message=msg)
        logger.info(msg)

        try:
            self._stop_heartbeats()

            # Delay the execution for a small random amount of time if this is our
            # first run. This will slightly skew the rendezvous attempts across the
            # nodes and reduce the load on the backend.
            if self._state_holder.state.round == 0:
                _delay(seconds=(0, 0.3))

            exit_op = _RendezvousExitOp()
            join_op = _RendezvousJoinOp()

            deadline = self._get_deadline(self._settings.timeout.join)
            self._op_executor.run(exit_op, deadline)
            self._op_executor.run(join_op, deadline, self._get_deadline)

            self._start_heartbeats()

            rank, world_size = self._get_world()
            store = self._get_store()

        except Exception as e:
            self._record(
                message=f"{type(e).__name__}: {str(e)}",
                node_state=NodeState.FAILED,
            )
            raise

        msg = (
            f"The node '{self._this_node}' has joined round {self._state_holder.state.round} of "
            f"the rendezvous '{self._settings.run_id}' as rank {rank} in a world of size "
            f"{world_size}."
        )
        self._record(message=msg, rank=rank)
        logger.info(msg)

        # opt-out option of TCPStore sharing
        if os.getenv("TORCH_DISABLE_SHARE_RDZV_TCP_STORE", "0") == "1":
            bootstrap_store_info = RendezvousStoreInfo.build(
                rank, store, local_addr=self._this_node.addr
            )
            return RendezvousInfo(
                store,
                rank,
                world_size,
                bootstrap_store_info,
            )

        # This will only be hit when TCPStore sharing is enabled.
        if self._bootstrap_store_info is None:
            # To avoid race in get_free_port because we release the port after the call,
            # we want to create a TCPStore server soon afterwards.
            server_port = 0
            if rank == 0:
                self._shared_tcp_store_server = self._create_tcp_store_server(
                    self._this_node.addr, server_port
                )
                server_port = self._shared_tcp_store_server.port
            self._bootstrap_store_info = RendezvousStoreInfo.build(
                rank,
                store,
                local_addr=self._this_node.addr,
                server_port=server_port,  # For non-0 rank, this is a no-op
            )

        if self._bootstrap_store_info is None:
            raise AssertionError
        if rank == 0:
            if self._shared_tcp_store_server is None:
                raise AssertionError

        return RendezvousInfo(
            store,
            rank,
            world_size,
            self._bootstrap_store_info,  # type: ignore[assignment]
        )