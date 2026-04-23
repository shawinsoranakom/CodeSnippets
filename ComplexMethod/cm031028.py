def test_many_subthreads_can_handle_pending_calls(self):
        main_tid = threading.get_ident()
        self.assertEqual(threading.main_thread().ident, main_tid)

        # We can't use queue.Queue since it isn't reentrant relative
        # to pending calls.
        _queue = deque()
        _active = deque()
        _done_lock = threading.Lock()
        def queue_put(task):
            _queue.append(task)
            _active.append(True)
        def queue_get():
            try:
                task = _queue.popleft()
            except IndexError:
                raise queue.Empty
            return task
        def queue_task_done():
            _active.pop()
            if not _active:
                try:
                    _done_lock.release()
                except RuntimeError:
                    assert not _done_lock.locked()
        def queue_empty():
            return not _queue
        def queue_join():
            _done_lock.acquire()
            _done_lock.release()

        tasks = []
        for i in range(20):
            task = self.PendingTask(
                req=f'request {i}',
                taskid=i,
                notify_done=queue_task_done,
            )
            tasks.append(task)
            queue_put(task)
        # This will be released once all the tasks have finished.
        _done_lock.acquire()

        def add_tasks(worker_tids):
            while True:
                if done:
                    return
                try:
                    task = queue_get()
                except queue.Empty:
                    break
                task.run_in_pending_call(worker_tids)

        done = False
        def run_tasks():
            while not queue_empty():
                if done:
                    return
                time.sleep(0.01)
            # Give the worker a chance to handle any remaining pending calls.
            while not done:
                time.sleep(0.01)

        # Start the workers and wait for them to finish.
        worker_threads = [threading.Thread(target=run_tasks)
                          for _ in range(3)]
        with threading_helper.start_threads(worker_threads):
            try:
                # Add a pending call for each task.
                worker_tids = [t.ident for t in worker_threads]
                threads = [threading.Thread(target=add_tasks, args=(worker_tids,))
                           for _ in range(3)]
                with threading_helper.start_threads(threads):
                    try:
                        pass
                    except BaseException:
                        done = True
                        raise  # re-raise
                # Wait for the pending calls to finish.
                queue_join()
                # Notify the workers that they can stop.
                done = True
            except BaseException:
                done = True
                raise  # re-raise
        runner_tids = [t.runner_tid for t in tasks]

        self.assertNotIn(main_tid, runner_tids)
        for task in tasks:
            with self.subTest(f'task {task.id}'):
                self.assertNotEqual(task.requester_tid, main_tid)
                self.assertNotEqual(task.requester_tid, task.runner_tid)
                self.assertNotIn(task.requester_tid, runner_tids)