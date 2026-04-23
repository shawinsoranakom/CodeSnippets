def _terminate_broken(self, cause):
        # Terminate the executor because it is in a broken state. The cause
        # argument can be used to display more information on the error that
        # lead the executor into becoming broken.

        # Mark the process pool broken so that submits fail right now.
        executor = self.executor_reference()
        if executor is not None:
            executor._broken = ('A child process terminated '
                                'abruptly, the process pool is not '
                                'usable anymore')
            executor._shutdown_thread = True
            executor = None

        # All pending tasks are to be marked failed with the following
        # BrokenProcessPool error
        bpe = BrokenProcessPool("A process in the process pool was "
                                "terminated abruptly while the future was "
                                "running or pending.")
        cause_str = None
        if cause is not None:
            cause_str = ''.join(cause)
        else:
            # No cause known, so report any processes that have
            # terminated with nonzero exit codes, e.g. from a
            # segfault. Multiple may terminate simultaneously,
            # so include all of them in the traceback.
            errors = []
            for p in self.processes.values():
                if p.exitcode is not None and p.exitcode != 0:
                    errors.append(f"Process {p.pid} terminated abruptly "
                                  f"with exit code {p.exitcode}")
            if errors:
                cause_str = "\n".join(errors)
        if cause_str:
            bpe.__cause__ = _RemoteTraceback(f"\n'''\n{cause_str}'''")

        # Mark pending tasks as failed.
        for work_id, work_item in self.pending_work_items.items():
            try:
                work_item.future.set_exception(bpe)
            except _base.InvalidStateError:
                # set_exception() fails if the future is cancelled: ignore it.
                # Trying to check if the future is cancelled before calling
                # set_exception() would leave a race condition if the future is
                # cancelled between the check and set_exception().
                pass
            # Delete references to object. See issue16284
            del work_item
        self.pending_work_items.clear()

        # Terminate remaining workers forcibly: the queues or their
        # locks may be in a dirty state and block forever.
        for p in self.processes.values():
            p.terminate()

        self.call_queue._terminate_broken()

        # clean up resources
        self._join_executor_internals(broken=True)