def validate_task(self, task):
        """
        Determine whether the provided Task can be executed by the backend.
        """
        if not is_module_level_function(task.func):
            raise InvalidTask("Task function must be defined at a module level.")

        if not self.supports_async_task and iscoroutinefunction(task.func):
            raise InvalidTask("Backend does not support async Tasks.")

        task_func_args = get_func_args(task.func)
        if task.takes_context and (
            not task_func_args or task_func_args[0] != "context"
        ):
            raise InvalidTask(
                "Task takes context but does not have a first argument of 'context'."
            )

        if not self.supports_priority and task.priority != DEFAULT_TASK_PRIORITY:
            raise InvalidTask("Backend does not support setting priority of tasks.")
        if (
            task.priority < TASK_MIN_PRIORITY
            or task.priority > TASK_MAX_PRIORITY
            or int(task.priority) != task.priority
        ):
            raise InvalidTask(
                f"priority must be a whole number between {TASK_MIN_PRIORITY} and "
                f"{TASK_MAX_PRIORITY}."
            )

        if not self.supports_defer and task.run_after is not None:
            raise InvalidTask("Backend does not support run_after.")

        if (
            settings.USE_TZ
            and task.run_after is not None
            and not timezone.is_aware(task.run_after)
        ):
            raise InvalidTask("run_after must be an aware datetime.")

        if self.queues and task.queue_name not in self.queues:
            raise InvalidTask(f"Queue '{task.queue_name}' is not valid for backend.")