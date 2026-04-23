async def run_one_coro(ok_to_start, previous_failed) -> None:
        # in eager tasks this waits for the calling task to append this task
        # to running_tasks, in regular tasks this wait is a no-op that does
        # not yield a future. See gh-124309.
        await ok_to_start.wait()
        # Wait for the previous task to finish, or for delay seconds
        if previous_failed is not None:
            with contextlib.suppress(exceptions_mod.TimeoutError):
                # Use asyncio.wait_for() instead of asyncio.wait() here, so
                # that if we get cancelled at this point, Event.wait() is also
                # cancelled, otherwise there will be a "Task destroyed but it is
                # pending" later.
                await tasks.wait_for(previous_failed.wait(), delay)
        # Get the next coroutine to run
        try:
            this_index, coro_fn = next(enum_coro_fns)
        except StopIteration:
            return
        # Start task that will run the next coroutine
        this_failed = locks.Event()
        next_ok_to_start = locks.Event()
        next_task = loop.create_task(run_one_coro(next_ok_to_start, this_failed))
        futures.future_add_to_awaited_by(next_task, parent_task)
        running_tasks.add(next_task)
        next_task.add_done_callback(task_done)
        # next_task has been appended to running_tasks so next_task is ok to
        # start.
        next_ok_to_start.set()
        # Prepare place to put this coroutine's exceptions if not won
        exceptions.append(None)
        assert len(exceptions) == this_index + 1

        try:
            result = await coro_fn()
        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException as e:
            exceptions[this_index] = e
            this_failed.set()  # Kickstart the next coroutine
        else:
            # Store winner's results
            nonlocal winner_index, winner_result
            assert winner_index is None
            winner_index = this_index
            winner_result = result
            # Cancel all other tasks. We take care to not cancel the current
            # task as well. If we do so, then since there is no `await` after
            # here and CancelledError are usually thrown at one, we will
            # encounter a curious corner case where the current task will end
            # up as done() == True, cancelled() == False, exception() ==
            # asyncio.CancelledError. This behavior is specified in
            # https://bugs.python.org/issue30048
            current_task = tasks.current_task(loop)
            for t in running_tasks:
                if t is not current_task:
                    t.cancel()