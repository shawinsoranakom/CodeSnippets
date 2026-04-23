def receive(
        self,
        num_messages: int = 1,
        wait_time_seconds: int = None,
        visibility_timeout: int = None,
        *,
        poll_empty_queue: bool = False,
    ) -> ReceiveMessageResult:
        result = ReceiveMessageResult()

        max_receive_count = self.max_receive_count
        visibility_timeout = (
            self.visibility_timeout if visibility_timeout is None else visibility_timeout
        )

        block = True if wait_time_seconds else False
        timeout = wait_time_seconds or 0
        start = time.time()

        # collect messages
        while True:
            try:
                message = self.visible.get(block=block, timeout=timeout)
            except Empty:
                break
            # setting block to false guarantees that, if we've already waited before, we don't wait the
            # full time again in the next iteration if max_number_of_messages is set but there are no more
            # messages in the queue. see https://github.com/localstack/localstack/issues/5824
            if not poll_empty_queue:
                block = False

            timeout -= time.time() - start
            if timeout < 0:
                timeout = 0

            if message.deleted:
                # filter messages that were deleted with an expired receipt handle after they have been
                # re-queued. this can only happen due to a race with `remove`.
                continue

            # update message attributes
            message.receive_count += 1
            message.update_visibility_timeout(visibility_timeout)
            message.set_last_received(time.time())
            if message.first_received is None:
                message.first_received = message.last_received

            LOG.debug("de-queued message %s from %s", message, self.arn)
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

                # now we can return
                if len(result.successful) == num_messages:
                    break

        # now process the successful result messages: create receipt handles and manage visibility.
        for message in result.successful:
            # manage receipt handle
            receipt_handle = self.create_receipt_handle(message)
            message.receipt_handles.add(receipt_handle)
            self.receipts[receipt_handle] = message
            result.receipt_handles.append(receipt_handle)

            # manage message visibility
            if message.visibility_timeout == 0:
                self.visible.put_nowait(message)
            else:
                self.add_inflight_message(message)

        return result