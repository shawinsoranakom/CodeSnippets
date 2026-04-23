def get_next_element_by_instance(self, instance_id: int):
        if self._datapipe_iterator is None and self._child_stop[instance_id]:
            self._datapipe_iterator = iter(self.main_datapipe)
            self._snapshot_state = _SnapshotState.Iterating
            for i in range(self.num_instances):
                self._child_stop[i] = False
        try:
            while not self._child_stop[instance_id]:
                self.child_pointers[instance_id] += 1
                if (
                    self.end_ptr is not None
                    and self.child_pointers[instance_id] == self.end_ptr
                ):
                    self._child_stop[instance_id] = True
                    break
                # Use buffer
                if self.buffer and self.child_pointers[instance_id] <= self.leading_ptr:
                    idx = self.child_pointers[instance_id] - self.slowest_ptr - 1
                    return_val = self.buffer[idx]
                else:  # Retrieve one element from main datapipe
                    self.leading_ptr = self.child_pointers[instance_id]
                    try:
                        return_val = next(self._datapipe_iterator)  # type: ignore[arg-type]
                        self.buffer.append(return_val)
                    except StopIteration:
                        self._child_stop[instance_id] = True
                        self._datapipe_iterator = None
                        self.end_ptr = self.leading_ptr
                        continue
                if self.child_pointers[instance_id] == self.slowest_ptr + 1:
                    new_min = min(
                        self.child_pointers
                    )  # Can optimize by avoiding the call to min()
                    if self.slowest_ptr < new_min:
                        self.slowest_ptr = new_min
                        self.buffer.popleft()
                if (
                    self.buffer_size >= 0
                    and self.leading_ptr > self.buffer_size + self.slowest_ptr
                ):
                    raise BufferError(
                        "ForkerIterDataPipe buffer overflow,"
                        + f"buffer size {self.buffer_size} is insufficient."
                    )

                yield self.copy_fn(return_val)  # type: ignore[possibly-undefined]
        finally:
            self._child_stop[instance_id] = True
            # Cleanup _datapipe_iterator for the case that fork exits earlier
            if all(self._child_stop):
                self._datapipe_iterator = None
                self._cleanup()