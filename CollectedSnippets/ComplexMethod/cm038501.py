def update_connector_output(self, connector_output: KVConnectorOutput):
        """
        Update KVConnector state from worker-side connectors output.

        Args:
            connector_output (KVConnectorOutput): the worker-side
                connectors output.
        """
        for req_id in connector_output.finished_sending or []:
            keys = self._reqs_being_stored.pop(req_id, None)
            if keys:
                self.manager.complete_store(keys)

        for req_id in connector_output.finished_recving or []:
            keys = self._reqs_being_loaded.pop(req_id, None)
            if keys:
                if self._blocks_being_loaded:
                    self._blocks_being_loaded.difference_update(keys)
                self.manager.complete_load(keys)