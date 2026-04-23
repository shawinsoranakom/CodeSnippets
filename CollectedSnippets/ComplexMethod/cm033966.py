def _queue_task(self, host, task, task_vars, play_context):
        """ handles queueing the task up to be sent to a worker """

        display.debug("entering _queue_task() for %s/%s" % (host.name, task.action))

        # create a templar and template things we need later for the queuing process
        templar = TemplateEngine(loader=self._loader, variables=task_vars)

        try:
            throttle = int(templar.template(task.throttle))
        except Exception as ex:
            raise AnsibleError("Failed to convert the throttle value to an integer.", obj=task.throttle) from ex

        # and then queue the new task
        try:
            # Determine the "rewind point" of the worker list. This means we start
            # iterating over the list of workers until the end of the list is found.
            # Normally, that is simply the length of the workers list (as determined
            # by the forks or serial setting), however a task/block/play may "throttle"
            # that limit down.
            rewind_point = len(self._workers)
            if throttle > 0 and self.ALLOW_BASE_THROTTLING:
                if task.run_once:
                    display.debug("Ignoring 'throttle' as 'run_once' is also set for '%s'" % task.get_name())
                else:
                    if throttle <= rewind_point:
                        display.debug("task: %s, throttle: %d" % (task.get_name(), throttle))
                        rewind_point = throttle

            queued = False
            starting_worker = self._cur_worker
            while True:
                self._process_rpc_queue()

                if self._cur_worker >= rewind_point:
                    self._cur_worker = 0

                worker_prc = self._workers[self._cur_worker]
                if worker_prc is None or not worker_prc.is_alive():
                    if worker_prc:
                        worker_prc.close()
                    self._queued_task_cache[(host.name, task._uuid)] = {
                        'host': host,
                        'task': task,
                        'task_vars': task_vars,
                        'play_context': play_context
                    }

                    # Pass WorkerProcess its strategy worker number so it can send an identifier along with intra-task requests
                    worker_prc = WorkerProcess(
                        final_q=self._final_q,
                        task_vars=task_vars,
                        host=host,
                        task=task,
                        play_context=play_context,
                        loader=self._loader,
                        variable_manager=self._variable_manager,
                        shared_loader_obj=plugin_loader.get_plugin_loader_namespace(),
                        worker_id=self._cur_worker,
                        cliargs=context.CLIARGS,
                    )
                    self._workers[self._cur_worker] = worker_prc
                    self._tqm.send_callback('v2_runner_on_start', host, task)
                    worker_prc.start()
                    display.debug("worker is %d (out of %d available)" % (self._cur_worker + 1, len(self._workers)))
                    queued = True

                self._cur_worker += 1

                if self._cur_worker >= rewind_point:
                    self._cur_worker = 0

                if queued:
                    break
                elif self._cur_worker == starting_worker:
                    time.sleep(0.0001)

            self._pending_results += 1
        except (EOFError, OSError, AssertionError) as ex:
            # most likely an abort
            display.debug(f"got an error while queuing: {ex}")
            return
        display.debug("exiting _queue_task() for %s/%s" % (host.name, task.action))