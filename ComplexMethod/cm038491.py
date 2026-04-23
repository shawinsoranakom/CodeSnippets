def build_connector_meta(
        self,
        scheduler_output: SchedulerOutput,
    ) -> KVConnectorMetadata:
        meta = MoRIIOConnectorMetadata()
        meta.transfer_id_to_request_id = self.transfer_id_to_request_id

        if self.mode == MoRIIOMode.WRITE:
            # when async_load_kv finished,
            # new reqs will be added to scheduler_output.scheduled_new_reqs

            if get_role() == ROLE.CONSUMER:
                for new_req in scheduler_output.scheduled_new_reqs:
                    red_id = new_req.req_id
                    local_block_ids = list(new_req.block_ids)[0]
                    assert new_req.sampling_params is not None, (
                        f"sampling_params is None for req {new_req.req_id}"
                    )
                    assert hasattr(new_req.sampling_params, "extra_args"), (
                        f"sampling_params missing extra_args for req {new_req.req_id}"
                    )
                    kv_transfer_params = (
                        new_req.sampling_params.extra_args.get("kv_transfer_params", {})
                        if new_req.sampling_params.extra_args
                        else {}
                    )
                    meta.add_new_req(
                        red_id,
                        local_block_ids,
                        kv_transfer_params,
                    )
            if get_role() == ROLE.PRODUCER:
                # This is the logic for checking against chunked prefill.
                # When the last chunk is identified,
                # It places the request metadata into the saving queue.

                for i, req_id in enumerate(
                    scheduler_output.scheduled_cached_reqs.req_ids
                ):
                    new_block_ids = (
                        scheduler_output.scheduled_cached_reqs.new_block_ids[i]
                    )

                    if new_block_ids is not None:
                        block_ids = new_block_ids[0]
                        # TODO : hybrid attn, etc
                        req, existing_blocks = self._reqs_need_pending_save[req_id]
                        updated_blocks = list(existing_blocks) + (block_ids)
                        self._reqs_need_pending_save[req_id] = (req, updated_blocks)
                        if (
                            len(self._reqs_need_pending_save[req_id][1])
                            * self.block_size
                            >= req.num_prompt_tokens
                        ):
                            meta.add_new_req(
                                request_id=req_id,
                                local_block_ids=self._reqs_need_pending_save[req_id][1],
                                kv_transfer_params=req.kv_transfer_params or {},
                                write_mode=True,
                            )
                            del self._reqs_need_pending_save[req_id]

        # Loop through scheduled reqs and convert to ReqMeta.
        for req_id, (req, block_ids) in self._reqs_need_recv.items():
            assert req.kv_transfer_params is not None
            meta.add_new_req(
                request_id=req_id,
                local_block_ids=block_ids,
                kv_transfer_params=req.kv_transfer_params,
            )

        for req_id, (req, block_ids) in self._reqs_need_save.items():
            assert req.kv_transfer_params is not None
            if req.num_prompt_tokens > len(block_ids) * self.block_size:
                # not last chunk prefill
                self._reqs_need_pending_save[req_id] = (req, block_ids)
                continue
            meta.add_new_req(
                request_id=req_id,
                local_block_ids=block_ids,
                kv_transfer_params=req.kv_transfer_params,
                write_mode=True,
            )
        # Clear the list once workers start the transfers

        meta.reqs_to_send = self._reqs_need_send

        self._reqs_need_recv.clear()
        self._reqs_need_save.clear()
        self._reqs_need_send = {}

        return meta