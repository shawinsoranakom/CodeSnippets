def _read_thread(self) -> None:
        while True:
            data = b""
            job_id = -1
            try:
                msg_header, job_id, data = _recv_msg(self.read_pipe)
            except Exception:
                # Something went wrong during the read. There's no way we have a
                # valid msg.
                log.exception("failure in subproc_pool._recv_msg")
                msg_header = MsgHeader.ERROR

            if msg_header != MsgHeader.JOB:
                # read_pipe returned None or got exception
                if self.running:
                    log.warning("SubprocPool unclean exit")
                    self.running = False
                    self.running_waitcounter.__exit__()
                self.read_pipe.close()
                # Cancel all the pending futures.
                self.shutdown()
                return

            try:
                result = self.pickler.loads(data)
            except Exception as e:
                # Something went wrong unpickling. We have a job_id so just
                # notify that particular future and continue on.
                log.exception("unpickle failure in SubprocPool._read_thread")
                result = e

            with self.futures_lock:
                if not self.running:
                    return
                if self.timer:
                    self.timer.record_call()
                if isinstance(result, _SubprocExceptionInfo):
                    # An exception occurred in the submitted job
                    self.pending_futures[job_id].set_exception(
                        SubprocException(result.details)
                    )
                elif isinstance(result, Exception):
                    # An exception occurred in some of our subprocess machinery.
                    self.pending_futures[job_id].set_exception(result)
                else:
                    self.pending_futures[job_id].set_result(result)

                self.pending_waitcounters[job_id].__exit__()
                del self.pending_waitcounters[job_id]
                if self.firstjob_id == job_id:
                    self.firstjob_waitcounter.__exit__()

                del self.pending_futures[job_id]