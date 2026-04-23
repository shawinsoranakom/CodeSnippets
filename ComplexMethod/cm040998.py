def start_message_move_task(
        self,
        context: RequestContext,
        source_arn: String,
        destination_arn: String = None,
        max_number_of_messages_per_second: NullableInteger = None,
        **kwargs,
    ) -> StartMessageMoveTaskResult:
        try:
            self._require_queue_by_arn(context, source_arn)
        except QueueDoesNotExist as e:
            raise ResourceNotFoundException(
                "The resource that you specified for the SourceArn parameter doesn't exist.",
                status_code=404,
            ) from e

        # check that the source queue is the dlq of some other queue
        is_dlq = False
        for _, _, store in sqs_stores.iter_stores():
            for queue in store.queues.values():
                if not queue.redrive_policy:
                    continue
                if queue.redrive_policy.get("deadLetterTargetArn") == source_arn:
                    is_dlq = True
                    break
            if is_dlq:
                break
        if not is_dlq:
            raise InvalidParameterValueException(
                "Source queue must be configured as a Dead Letter Queue."
            )

        # If destination_arn is left blank, the messages will be redriven back to their respective original
        # source queues.
        if destination_arn:
            try:
                self._require_queue_by_arn(context, destination_arn)
            except QueueDoesNotExist as e:
                raise ResourceNotFoundException(
                    "The resource that you specified for the DestinationArn parameter doesn't exist.",
                    status_code=404,
                ) from e

        # check that only one active task exists
        with self._message_move_task_manager.mutex:
            store = self.get_store(context.account_id, context.region)
            tasks = [
                task
                for task in store.move_tasks.values()
                if task.source_arn == source_arn
                and task.status
                in [
                    MessageMoveTaskStatus.CREATED,
                    MessageMoveTaskStatus.RUNNING,
                    MessageMoveTaskStatus.CANCELLING,
                ]
            ]
            if len(tasks) > 0:
                raise InvalidParameterValueException(
                    "There is already a task running. Only one active task is allowed for a source queue "
                    "arn at a given time."
                )

            task = MessageMoveTask(
                source_arn,
                destination_arn,
                max_number_of_messages_per_second,
            )
            store.move_tasks[task.task_id] = task

        self._message_move_task_manager.submit(task)

        return StartMessageMoveTaskResult(TaskHandle=task.task_handle)