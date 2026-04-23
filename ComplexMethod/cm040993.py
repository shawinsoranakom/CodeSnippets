def _run(self, move_task: MessageMoveTask):
        try:
            if move_task.destination_arn:
                LOG.info(
                    "Move task started %s (%s -> %s)",
                    move_task.task_id,
                    move_task.source_arn,
                    move_task.destination_arn,
                )
            else:
                LOG.info(
                    "Move task started %s (%s -> original sources)",
                    move_task.task_id,
                    move_task.source_arn,
                )

            while not move_task.cancel_event.is_set():
                # look up queues for every message in case they are removed
                source_queue = self._get_queue_by_arn(move_task.source_arn)

                receive_result = source_queue.receive(num_messages=1, visibility_timeout=1)

                if receive_result.dead_letter_messages:
                    raise NotImplementedError("Cannot deal with DLQ chains in move tasks")

                if not receive_result.successful:
                    # queue empty, task done
                    break

                message = receive_result.successful[0]
                receipt_handle = receive_result.receipt_handles[0]

                if move_task.destination_arn:
                    target_queue = self._get_queue_by_arn(move_task.destination_arn)
                else:
                    # we assume that dead_letter_source_arn is set since the message comes from a DLQ
                    target_queue = self._get_queue_by_arn(message.dead_letter_queue_source_arn)

                target_queue.put(
                    message=message.message,
                    message_group_id=message.message_group_id,
                    message_deduplication_id=message.message_deduplication_id,
                )
                source_queue.remove(receipt_handle)
                move_task.approximate_number_of_messages_moved += 1

                if rate := move_task.max_number_of_messages_per_second:
                    move_task.cancel_event.wait(timeout=(1 / rate))

        except Exception as e:
            self._fail_task(move_task, e)
        else:
            if move_task.cancel_event.is_set():
                LOG.info("Move task cancelled %s", move_task.task_id)
                move_task.status = MessageMoveTaskStatus.CANCELLED
            else:
                LOG.info("Move task completed successfully %s", move_task.task_id)
                move_task.status = MessageMoveTaskStatus.COMPLETED