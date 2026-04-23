def update_state_after_alloc(
        self,
        request: "Request",
        blocks: "KVCacheBlocks",
        num_external_tokens: int,
        connector_worker: "MoRIIOConnectorWorker | None" = None,
    ):
        params = request.kv_transfer_params
        if not params:
            return
        transfer_id = params["transfer_id"]
        request_id = request.request_id
        self.map_request_id(request_id, transfer_id)
        if params.get("do_remote_decode"):
            local_block_ids = blocks.get_block_ids()[0]
            self._reqs_need_save[request.request_id] = (request, local_block_ids)

        if params is not None and params.get("do_remote_prefill"):
            if self.mode == MoRIIOMode.READ:
                if remote_block_ids := params.get("remote_block_ids"):
                    # remote_engine_id is returned by the prefill's request_finished.
                    # host/ports come from the request_id (parsed in add_new_req).
                    if "remote_engine_id" in params:
                        # If remote_blocks and num_external_tokens = 0, we have
                        # a full prefix cache hit on the D worker. We need to call
                        # send_notify in _read_blocks to free the memory on the P.

                        # Get unhashed blocks to pull from remote.
                        local_block_ids = blocks.get_block_ids()[0]
                        assert len(local_block_ids) <= len(remote_block_ids)
                        if len(local_block_ids) == len(remote_block_ids):
                            pass
                        else:
                            local_block_ids = remote_block_ids[-len(local_block_ids) :]

                        self._reqs_need_recv[request.request_id] = (
                            request,
                            local_block_ids,
                        )
                    else:
                        logger.warning(
                            "Got invalid KVTransferParams: %s. This "
                            "request will not utilize KVTransfer",
                            params,
                        )

            else:
                # WRITE mode: prefill scheduler notifies the decode side that
                # blocks are ready.  Parse the decode's host/notify_port from
                # the request_id
                assert request.kv_transfer_params is not None, (
                    "kv_transfer_params should not be None"
                )

                remote_dp_rank = request.kv_transfer_params.get("remote_dp_rank", 0)

                peer_zmq = get_peer_zmq_from_request_id(
                    request.request_id, is_producer=True
                )
                remote_host, _, remote_notify_port = parse_moriio_zmq_address(peer_zmq)

                for tp_index in range(self.tp_size):
                    target_port = remote_notify_port + get_port_offset(
                        remote_dp_rank, tp_index
                    )

                    self.send_notify_block(
                        req_id=request.request_id,
                        transfer_id=request.kv_transfer_params["transfer_id"],
                        block_notify_list=blocks.get_block_ids()[0],
                        host=remote_host,
                        port=target_port,
                    )

            # Only trigger 1 KV transfer per request.

            params["do_remote_prefill"] = False