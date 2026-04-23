def list_message_move_tasks(
        self,
        context: RequestContext,
        source_arn: String,
        max_results: NullableInteger = None,
        **kwargs,
    ) -> ListMessageMoveTasksResult:
        try:
            self._require_queue_by_arn(context, source_arn)
        except InvalidArnException:
            raise InvalidParameterValueException(
                "You must use this format to specify the SourceArn: arn:<partition>:<service>:<region>:<account-id>:<resource-id>"
            )
        except QueueDoesNotExist:
            raise ResourceNotFoundException(
                "The resource that you specified for the SourceArn parameter doesn't exist."
            )

        # get move tasks for queue and sort them by most-recent
        store = self.get_store(context.account_id, context.region)
        tasks = [
            move_task
            for move_task in store.move_tasks.values()
            if move_task.source_arn == source_arn
            and move_task.status != MessageMoveTaskStatus.CREATED
        ]
        tasks.sort(key=lambda t: t.started_timestamp, reverse=True)

        # convert to result list
        n = max_results or 1
        return ListMessageMoveTasksResult(
            Results=[self._to_message_move_task_entry(task) for task in tasks[:n]]
        )