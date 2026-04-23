def _cleanup_load_request(self, req_id: str) -> None:
        """Release all load resources for a request.

        Shared between request_finished() and update_connector_output() paths.
        Removes the request from _reqs_to_load, cleans up event mappings,
        and frees CPU/GPU touch refs.
        """
        state = self._reqs_to_load.pop(req_id, None)
        if state is None:
            return
        # Remove from load event mapping (only this req, not whole event)
        if state.load_event is not None:
            reqs = self._load_event_to_reqs.get(state.load_event)
            if reqs is not None:
                with contextlib.suppress(ValueError):
                    reqs.remove(req_id)
                if not reqs:
                    self._load_event_to_reqs.pop(state.load_event, None)

        if state.transfer_meta is not None:
            # Free CPU touch refs
            self.cpu_block_pool.free_blocks(
                self.cpu_block_pool.blocks[bid]
                for bid in state.transfer_meta.cpu_block_ids
            )
            # Free GPU touch refs
            assert self._gpu_block_pool is not None
            self._gpu_block_pool.free_blocks(
                self._gpu_block_pool.blocks[bid]
                for bid in state.transfer_meta.gpu_block_ids
            )