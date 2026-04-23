def shutdown(self):
        """Shutdown the connector worker."""
        if not hasattr(self, "_handshake_initiation_executor"):
            # error happens during init, no need to shutdown
            return
        self._handshake_initiation_executor.shutdown(wait=False)
        for handles in self._recving_transfers.values():
            for handle in handles:
                self.nixl_wrapper.release_xfer_handle(handle)
        self._recving_transfers.clear()
        for handle in self.src_xfer_handles_by_block_size.values():
            self.nixl_wrapper.release_dlist_handle(handle)
        self.src_xfer_handles_by_block_size.clear()
        for handles in self.src_xfer_handles_by_tp_ratio.values():
            for handle in handles:
                self.nixl_wrapper.release_dlist_handle(handle)
        self.src_xfer_handles_by_tp_ratio.clear()
        for dst_xfer_side_handles in self.dst_xfer_side_handles.values():
            for dst_xfer_side_handle in dst_xfer_side_handles.values():
                self.nixl_wrapper.release_dlist_handle(dst_xfer_side_handle)
        self.dst_xfer_side_handles.clear()
        for remote_agents in self._remote_agents.values():
            for agent_name in remote_agents.values():
                self.nixl_wrapper.remove_remote_agent(agent_name)
        self._remote_agents.clear()
        for desc in self._registered_descs:
            self.nixl_wrapper.deregister_memory(desc)
        self._registered_descs.clear()