def put(
        self,
        message: Message,
        visibility_timeout: int = None,
        message_deduplication_id: str = None,
        message_group_id: str = None,
        delay_seconds: int = None,
    ):
        if delay_seconds:
            # in fifo queues, delay is only applied on queue level. However, explicitly setting delay_seconds=0 is valid
            raise InvalidParameterValueException(
                f"Value {delay_seconds} for parameter DelaySeconds is invalid. Reason: The request include parameter "
                f"that is not valid for this queue type."
            )

        if not message_group_id:
            raise MissingRequiredParameterException(
                "The request must contain the parameter MessageGroupId."
            )
        dedup_id = message_deduplication_id
        content_based_deduplication = not is_message_deduplication_id_required(self)
        if not dedup_id and content_based_deduplication:
            dedup_id = hashlib.sha256(message.get("Body").encode("utf-8")).hexdigest()
        if not dedup_id:
            raise InvalidParameterValueException(
                "The queue should either have ContentBasedDeduplication enabled or MessageDeduplicationId provided explicitly"
            )

        fifo_message = SqsMessage(
            time.time(),
            message,
            message_deduplication_id=dedup_id,
            message_group_id=message_group_id,
            sequence_number=str(self.next_sequence_number()),
        )
        if visibility_timeout is not None:
            fifo_message.visibility_timeout = visibility_timeout
        else:
            # use the attribute from the queue
            fifo_message.visibility_timeout = self.visibility_timeout

        # FIFO queues always use the queue level setting for 'DelaySeconds'
        fifo_message.delay_seconds = self.delay_seconds

        original_message = self.deduplication.get(dedup_id)
        if (
            original_message
            and original_message.priority + sqs_constants.DEDUPLICATION_INTERVAL_IN_SEC
            > fifo_message.priority
            # account for deduplication scope required for (but not restricted to) high-throughput-mode
            and (
                not self.deduplication_scope == "messageGroup"
                or fifo_message.message_group_id == original_message.message_group_id
            )
        ):
            message["MessageId"] = original_message.message["MessageId"]
        else:
            if fifo_message.is_delayed:
                self.delayed.add(fifo_message)
            else:
                self._put_message(fifo_message)

            self.deduplication[dedup_id] = fifo_message

        return fifo_message