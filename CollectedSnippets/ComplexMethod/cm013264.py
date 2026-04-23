def join(self, rank, data):
        with self._start_cond:
            self._data[rank] = data
            self._count += 1

            # notify rank 0
            if self._count == self._world_size:
                if rank > 0:
                    self._start_cond.notify()

            if rank == 0:
                self._start_cond.wait_for(
                    lambda: self._count == self._world_size
                    or self._pg._terminate.is_set()
                )
                # SystemExit is not a subclass of Exception but BaseException
                # and can be distinguished from normal exception raised from program errors
                # so that we can hide it from the exception queue
                if self._pg._terminate.is_set():
                    sys.exit("Test termination event occurs.")

        with self._done_cond:
            # wait for rank 0 to finish
            if rank > 0:
                self._done_cond.wait_for(
                    lambda: self._done or self._pg._terminate.is_set()
                )
                if self._pg._terminate.is_set():
                    sys.exit("Test termination event occurs.")
            else:
                # copy data around
                self._collective.work(self._data)
                self._done = True
                self._done_cond.notify_all()
        return ret_work(data)