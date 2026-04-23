def _execute_task(self, task_result):
        """
        Execute the Task for the given TaskResult, mutating it with the
        outcome.
        """
        object.__setattr__(task_result, "enqueued_at", timezone.now())
        task_enqueued.send(type(self), task_result=task_result)

        task = task_result.task
        task_start_time = timezone.now()
        object.__setattr__(task_result, "status", TaskResultStatus.RUNNING)
        object.__setattr__(task_result, "started_at", task_start_time)
        object.__setattr__(task_result, "last_attempted_at", task_start_time)
        task_result.worker_ids.append(self.worker_id)
        task_started.send(sender=type(self), task_result=task_result)

        try:
            if task.takes_context:
                raw_return_value = task.call(
                    TaskContext(task_result=task_result),
                    *task_result.args,
                    **task_result.kwargs,
                )
            else:
                raw_return_value = task.call(*task_result.args, **task_result.kwargs)

            object.__setattr__(
                task_result,
                "_return_value",
                normalize_json(raw_return_value),
            )
        except KeyboardInterrupt:
            # If the user tried to terminate, let them
            raise
        except BaseException as e:
            object.__setattr__(task_result, "finished_at", timezone.now())
            exception_type = type(e)
            task_result.errors.append(
                TaskError(
                    exception_class_path=(
                        f"{exception_type.__module__}.{exception_type.__qualname__}"
                    ),
                    traceback="".join(format_exception(e)),
                )
            )
            object.__setattr__(task_result, "status", TaskResultStatus.FAILED)
            task_finished.send(type(self), task_result=task_result)
        else:
            object.__setattr__(task_result, "finished_at", timezone.now())
            object.__setattr__(task_result, "status", TaskResultStatus.SUCCESSFUL)
            task_finished.send(type(self), task_result=task_result)