def receive(
        self,
        num_messages: int = 1,
        wait_time_seconds: int = None,
        visibility_timeout: int = None,
        *,
        poll_empty_queue: bool = False,
    ) -> ReceiveMessageResult:
        """
        Receive logic for FIFO queues is different from standard queues. See
        https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues-understanding-logic.html.

        When receiving messages from a FIFO queue with multiple message group IDs, SQS first attempts to
        return as many messages with the same message group ID as possible. This allows other consumers to
        process messages with a different message group ID. When you receive a message with a message group
        ID, no more messages for the same message group ID are returned unless you delete the message, or it
        becomes visible.
        """
        result = ReceiveMessageResult()

        max_receive_count = self.max_receive_count
        visibility_timeout = (
            self.visibility_timeout if visibility_timeout is None else visibility_timeout
        )

        block = True if wait_time_seconds else False
        timeout = wait_time_seconds or 0
        start = time.time()

        received_groups: set[MessageGroup] = set()

        # collect messages over potentially multiple groups
        while True:
            try:
                group: MessageGroup = self.message_group_queue.get(block=block, timeout=timeout)
            except Empty:
                break

            if group.empty():
                # this can be the case if all messages in the group are still invisible or
                # if all messages of a group have been processed.
                # TODO: it should be blocking until at least one message is in the queue, but we don't
                #  want to block the group
                # TODO: check behavior in case it happens if all messages were removed from a group due to message
                #  retention period.
                timeout -= time.time() - start
                if timeout < 0:
                    timeout = 0
                continue

            self.inflight_groups.add(group)

            received_groups.add(group)

            if not poll_empty_queue:
                block = False

            # we lock the queue while accessing the groups to not get into races with re-queueing/deleting
            with self.mutex:
                # collect messages from the group until a continue/break condition is met
                while True:
                    try:
                        message = group.pop()
                    except IndexError:
                        break

                    if message.deleted:
                        # this means the message was deleted with a receipt handle after its visibility
                        # timeout expired and the messages was re-queued in the meantime.
                        continue

                    # update message attributes
                    message.receive_count += 1
                    message.update_visibility_timeout(visibility_timeout)
                    message.set_last_received(time.time())
                    if message.first_received is None:
                        message.first_received = message.last_received

                    LOG.debug("de-queued message %s from fifo queue %s", message, self.arn)
                    if max_receive_count and message.receive_count > max_receive_count:
                        # the message needs to move to the DLQ
                        LOG.debug(
                            "message %s has been received %d times, marking it for DLQ",
                            message,
                            message.receive_count,
                        )
                        result.dead_letter_messages.append(message)
                    else:
                        result.successful.append(message)
                        message.increment_approximate_receive_count()

                        # now we can break the inner loop
                        if len(result.successful) == num_messages:
                            break

                # but we also need to check the condition to return from the outer loop
                if len(result.successful) == num_messages:
                    break

        # now process the successful result messages: create receipt handles and manage visibility.
        # we use the mutex again because we are modifying the group
        with self.mutex:
            for message in result.successful:
                # manage receipt handle
                receipt_handle = self.create_receipt_handle(message)
                message.receipt_handles.add(receipt_handle)
                self.receipts[receipt_handle] = message
                result.receipt_handles.append(receipt_handle)

                # manage message visibility
                if message.visibility_timeout == 0:
                    self._put_message(message)
                else:
                    self.add_inflight_message(message)
        return result