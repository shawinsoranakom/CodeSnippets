async def send_kv_to_decode(
        self, identity: bytes, sock: zmq.asyncio.Socket, meta: MooncakeXferMetadata
    ):
        pending_reqs: dict[ReqId, SendBlockMeta] = {}
        remote_tp_ranks = self.transfer_topo.handshake_target_ranks(meta.remote_tp_size)
        if meta.remote_tp_rank not in remote_tp_ranks:
            # This D worker does not pair with the P worker.
            msg = (
                "This D tp_rank "
                f"{meta.remote_tp_rank} is not paired with P tp_rank "
                f"{self.tp_rank}; expected one of {remote_tp_ranks}."
            )
            logger.error(msg)
            response = MooncakeXferResponse(
                status=MooncakeXferResponseStatus.ERROR,
                err_msg=msg,
            )
            await sock.send_multipart((identity, self._encoder.encode(response)))
            return
        local_regions = self._get_transfer_regions(
            self.kv_caches_base_addr, self.block_len_per_layer
        )
        remote_regions = self._get_transfer_regions(
            meta.kv_caches_base_addr, meta.block_lens
        )
        validation_err = _validate_asymmetric_region_lengths(
            local_regions=local_regions,
            remote_regions=remote_regions,
            local_tp_size=self.tp_size,
            remote_tp_size=meta.remote_tp_size,
            producer_cache_replicated=self._producer_cache_is_replicated(),
        )
        if validation_err is not None:
            response = MooncakeXferResponse(
                status=MooncakeXferResponseStatus.ERROR,
                err_msg=validation_err,
            )
            await sock.send_multipart((identity, self._encoder.encode(response)))
            return
        for d_req_id, (transfer_id, _) in meta.req_blocks.items():
            if transfer_id not in self.reqs_need_send:
                # This req is not enqueued in P side yet, create it here.
                self.reqs_need_send[transfer_id] = SendBlockMeta(
                    p_req_id="",
                    transfer_id=transfer_id,
                    local_block_ids=[],
                    ready=asyncio.Event(),
                )
            send_meta = self.reqs_need_send[transfer_id]
            pending_reqs[d_req_id] = send_meta

        async def wait_and_ret(
            d_req_id: ReqId, send_meta: SendBlockMeta
        ) -> tuple[ReqId, SendBlockMeta]:
            await send_meta.ready.wait()
            return d_req_id, send_meta

        wait_tasks = [
            asyncio.create_task(wait_and_ret(d_req_id, send_meta))
            for d_req_id, send_meta in pending_reqs.items()
        ]

        while wait_tasks:
            done, pending = await asyncio.wait(
                wait_tasks,
                timeout=envs.VLLM_MOONCAKE_ABORT_REQUEST_TIMEOUT,
                return_when=asyncio.FIRST_COMPLETED,
            )

            if not done:
                # Timeout, abort all pending requests.
                for task in wait_tasks:
                    task.cancel()
                logger.warning(
                    "Timeout waiting for P side ready: %s", list(pending_reqs)
                )
                response = MooncakeXferResponse(
                    status=MooncakeXferResponseStatus.FINISH,
                    err_reqs=list(pending_reqs),
                    err_msg="Timeout waiting for P side ready.",
                )
                await sock.send_multipart((identity, self._encoder.encode(response)))
                break

            wait_tasks = list(pending)
            response_status = (
                MooncakeXferResponseStatus.CONTINUE
                if wait_tasks
                else MooncakeXferResponseStatus.FINISH
            )
            ready_reqs: list[tuple[ReqId, SendBlockMeta]] = []
            for task in done:
                d_req_id, send_meta = task.result()
                del pending_reqs[d_req_id]
                # Do we still in reqs_need_send (not expired)?
                if send_meta.transfer_id in self.reqs_need_send:
                    # Mark it sending to avoid expiration.
                    send_meta.sending += 1
                    if not send_meta.need_send:
                        self.resolve_need_send(send_meta, remote_tp_ranks)
                    ready_reqs.append((d_req_id, send_meta))
                else:
                    # Otherwise (expired, very unlikely), just forget it.
                    logger.warning(
                        "Request %s expired before sending on P side.", d_req_id
                    )

            (
                src_ptrs,
                dst_ptrs,
                lengths,
                err_reqs,
                err_msg,
            ) = await self._build_transfer_params(
                ready_reqs,
                meta,
                local_regions,
                remote_regions,
            )
            err_req_set = set(err_reqs)
            ok_ready_reqs = [
                (d_req_id, send_meta)
                for d_req_id, send_meta in ready_reqs
                if d_req_id not in err_req_set
            ]

            if src_ptrs:
                remote_session = f"{meta.remote_hostname}:{meta.remote_port}"
                ret_value = await self.sender_loop.run_in_executor(
                    self._sender_executor,
                    self._send_blocks,
                    remote_session,
                    src_ptrs,
                    dst_ptrs,
                    lengths,
                )

                if ret_value != 0:
                    transfer_err_msg = f"Mooncake transfer engine returned {ret_value}"
                    err_msg = (
                        transfer_err_msg
                        if err_msg is None
                        else f"{err_msg}; {transfer_err_msg}"
                    )
                    err_reqs = list(err_reqs)
                    for d_req_id, _ in ok_ready_reqs:
                        err_reqs.append(d_req_id)
                        err_req_set.add(d_req_id)
                    ok_ready_reqs = []

            for d_req_id, send_meta in ready_reqs:
                send_meta.sending -= 1

                if d_req_id in err_req_set:
                    continue

                send_meta.sent += 1
                if (
                    send_meta.sent == send_meta.need_send
                    and self.reqs_need_send.pop(send_meta.transfer_id, None) is not None
                ):
                    self.finished_sending_reqs.add(send_meta.p_req_id)

            response = MooncakeXferResponse(
                status=response_status,
                ok_reqs=[d_req_id for d_req_id, _ in ok_ready_reqs] or None,
                err_reqs=err_reqs or None,
                err_msg=err_msg,
            )
            await sock.send_multipart((identity, self._encoder.encode(response)))