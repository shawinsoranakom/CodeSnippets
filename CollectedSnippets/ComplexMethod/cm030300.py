def run(self):
        # Main loop for the executor manager thread.

        while True:
            # gh-109047: During Python finalization, self.call_queue.put()
            # creation of a thread can fail with RuntimeError.
            try:
                self.add_call_item_to_queue()
            except BaseException as exc:
                cause = format_exception(exc)
                self.terminate_broken(cause)
                return

            result_item, is_broken, cause = self.wait_result_broken_or_wakeup()

            if is_broken:
                self.terminate_broken(cause)
                return
            if result_item is not None:
                self.process_result_item(result_item)

                process_exited = result_item.exit_pid is not None
                if process_exited:
                    p = self.processes.pop(result_item.exit_pid)
                    p.join()

                # Delete reference to result_item to avoid keeping references
                # while waiting on new results.
                del result_item

                if executor := self.executor_reference():
                    if process_exited:
                        with self.shutdown_lock:
                            executor._adjust_process_count()
                    else:
                        executor._idle_worker_semaphore.release()
                    del executor

            if self.is_shutting_down():
                self.flag_executor_shutting_down()

                # When only canceled futures remain in pending_work_items, our
                # next call to wait_result_broken_or_wakeup would hang forever.
                # This makes sure we have some running futures or none at all.
                self.add_call_item_to_queue()

                # Since no new work items can be added, it is safe to shutdown
                # this thread if there are no pending work items.
                if not self.pending_work_items:
                    self.join_executor_internals()
                    return