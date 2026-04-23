def get_next_element_by_instance(self, instance_id: int):
        if self._datapipe_iterator is None and self._child_stop[instance_id]:
            self._datapipe_iterator = iter(self.main_datapipe)
            self._snapshot_state = (
                _SnapshotState.Iterating
            )  # This is necessary for the DataPipe to reset properly.
            self.main_datapipe_exhausted = False
            for i in range(self.num_instances):
                self._child_stop[i] = False

        try:
            while not self._child_stop[instance_id]:
                if self.child_buffers[instance_id]:
                    self.current_buffer_usage -= 1
                    yield self.child_buffers[instance_id].popleft()
                else:
                    try:
                        yield self._find_next(instance_id)
                    except StopIteration:
                        self._child_stop[instance_id] = True
                        self.main_datapipe_exhausted = True
                        self._datapipe_iterator = None
        finally:
            self._child_stop[instance_id] = True
            # Cleanup _datapipe_iterator for the case that demux exits earlier
            if all(self._child_stop):
                self._datapipe_iterator = None
            if self.child_buffers[instance_id]:
                self._cleanup(instance_id)