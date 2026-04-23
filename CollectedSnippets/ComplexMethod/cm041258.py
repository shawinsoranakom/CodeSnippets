def run(self):
        q = self._queue
        cond = self._condition
        executor = self.executor
        poison = self.POISON

        task: ScheduledTask
        while True:
            deadline, task = q.get()

            if (deadline, task) == poison:
                break

            if task.is_cancelled:
                continue

            # wait until the task should be executed
            wait = max(0, deadline - time.time())
            if wait > 0:
                with cond:
                    interrupted = cond.wait(timeout=wait)
                    if interrupted:
                        # something with a potentially earlier deadline has arrived while waiting, so we re-queue and
                        # continue. this could be optimized by checking the deadline of the added element(s) first,
                        # but that would be fairly involved. the assumption is that `schedule` is not invoked frequently
                        q.put((task.deadline, task))
                        continue

            # run or submit the task
            if not task.is_cancelled:
                if executor:
                    executor.submit(task.run)
                else:
                    task.run()

            if task.is_periodic:
                try:
                    task.set_next_deadline()
                except ValueError:
                    # task deadline couldn't be set because it was cancelled
                    continue
                q.put((task.deadline, task))