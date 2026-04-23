def _next_data(self):
        while True:
            # If the worker responsible for `self._rcvd_idx` has already ended
            # and was unable to fulfill this task (due to exhausting an `IterableDataset`),
            # we try to advance `self._rcvd_idx` to find the next valid index.
            #
            # This part needs to run in the loop because both the `self._get_data()`
            # call and `_IterableDatasetStopIteration` check below can mark
            # extra worker(s) as dead.
            while self._rcvd_idx < self._send_idx:
                info = self._task_info.get(self._rcvd_idx, None)
                if info:
                    worker_id = info[0]
                    if (
                        len(info) == 2 or self._workers_status[worker_id]
                    ):  # has data or is still active
                        break
                    del self._task_info[self._rcvd_idx]
                self._rcvd_idx += 1
            else:
                # no valid `self._rcvd_idx` is found (i.e., didn't break)
                if not self._persistent_workers:
                    self._shutdown_workers()
                raise StopIteration

            # Now `self._rcvd_idx` is the batch index we want to fetch

            # Check if the next sample has already been generated
            if len(self._task_info[self._rcvd_idx]) == 2:
                worker_id, data = self._task_info.pop(self._rcvd_idx)
                self._rcvd_idx += 1
                return self._process_data(data, worker_id)

            if self._shutdown or self._tasks_outstanding <= 0:
                raise AssertionError(
                    "Invalid iterator state: shutdown or no outstanding tasks when fetching next data"
                )
            idx, data = self._get_data()
            self._tasks_outstanding -= 1
            if self._dataset_kind == _DatasetKind.Iterable:
                # Check for _IterableDatasetStopIteration
                if isinstance(data, _utils.worker._IterableDatasetStopIteration):
                    if self._persistent_workers:
                        self._workers_status[data.worker_id] = False
                    else:
                        self._mark_worker_as_unavailable(data.worker_id)
                    self._try_put_index()
                    continue

            if idx != self._rcvd_idx:
                if not self._in_order:
                    # don't store it for later, process now
                    # delete from self._task_info immediately
                    # this keeps the object size manageable
                    worker_id = self._task_info.pop(idx)[0]
                    return self._process_data(data, worker_id)
                # store out-of-order samples
                self._task_info[idx] += (data,)
            else:
                worker_id = self._task_info.pop(idx)[0]
                self._rcvd_idx += 1
                return self._process_data(data, worker_id)