def start_load_kv(self, metadata: MoRIIOConnectorMetadata):
        """
        Start loading by triggering non-blocking moriio_xfer.
        We check for these trnxs to complete in each step().
        """
        self.transfer_id_to_request_id = metadata.transfer_id_to_request_id
        if self.is_producer:
            self.moriio_wrapper.async_wait_reqid()
            return
        if self.mode == MoRIIOMode.WRITE:
            return

        wait_handshake_readd_req = False
        remote_engine_id = None

        for req_id, meta in metadata.reqs_to_recv.items():
            remote_engine_id = (
                str(meta.remote_host) + ":" + str(meta.remote_handshake_port)
            )
            meta.remote_engine_id = remote_engine_id
            dp0_remote_engine_id = self.get_engine_name_with_dp(remote_engine_id, 0)
            if dp0_remote_engine_id not in self._remote_agents:
                # Initiate handshake with remote engine to exchange metadata.
                with self._handshake_lock:
                    if remote_engine_id not in self._remote_agents:
                        self._background_moriio_handshake(
                            req_id, remote_engine_id, meta
                        )
                        wait_handshake_readd_req = True

                        continue

            # Handshake already completed, start async read xfer.
            self._read_blocks_for_req(req_id, meta)
        # Start transfers for requests whose handshakes have now finished.

        while True:
            if (
                self._ready_requests.empty()
                and remote_engine_id not in self.load_ready_flag
                and wait_handshake_readd_req
            ):
                continue
            elif (
                not self._ready_requests.empty()
                and remote_engine_id in self.load_ready_flag
            ):
                self._read_blocks_for_req(*self._ready_requests.get_nowait())
                break
            else:
                break

        self._reqs_to_send.update(metadata.reqs_to_send)