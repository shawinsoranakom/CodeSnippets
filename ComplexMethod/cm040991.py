def _collect_messages(
        self, queue: SqsQueue, show_invisible: bool = False, show_delayed: bool = False
    ) -> list[Message]:
        """
        Retrieves from a given SqsQueue all visible messages without causing any side effects (not setting any
        receive timestamps, receive counts, or visibility state).

        :param queue: the queue
        :param show_invisible: show invisible messages as well
        :param show_delayed: show delayed messages as well
        :return: a list of messages
        """
        receipt_handle = "SQS/BACKDOOR/ACCESS"  # dummy receipt handle

        sqs_messages: list[SqsMessage] = []

        if show_invisible:
            sqs_messages.extend(queue.inflight)

        if isinstance(queue, StandardQueue):
            sqs_messages.extend(queue.visible.queue)
        elif isinstance(queue, FifoQueue):
            if show_invisible:
                for inflight_group in queue.inflight_groups:
                    # messages that have been received are held in ``queue.inflight``, even for FIFO queues. however,
                    # for fifo queues, messages that are in the same message group as messages that have been
                    # received, are also considered invisible, and are held here in ``inflight_group.messages``.
                    for sqs_message in inflight_group.messages:
                        sqs_messages.append(sqs_message)

            for message_group in queue.message_group_queue.queue:
                # these are all messages of message groups that are visible
                for sqs_message in message_group.messages:
                    sqs_messages.append(sqs_message)
        else:
            raise ValueError(f"unknown queue type {type(queue)}")

        if show_delayed:
            sqs_messages.extend(queue.delayed)

        messages = []

        for sqs_message in sqs_messages:
            message: Message = to_sqs_api_message(sqs_message, [QueueAttributeName.All], ["All"])
            # these are all non-standard fields so we squelch the linter
            if show_invisible:
                message["Attributes"]["IsVisible"] = str(sqs_message.is_visible).lower()  # noqa
            if show_delayed:
                message["Attributes"]["IsDelayed"] = str(sqs_message.is_delayed).lower()  # noqa
            messages.append(message)
            message["ReceiptHandle"] = receipt_handle

        return messages