def handle_messages(self, messages):
        polled_events = transform_into_events(messages)
        # Filtering: matching vs. discarded (i.e., not matching filter criteria)
        # TODO: implement format detection behavior (e.g., for JSON body):
        #  https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-pipes-event-filtering.html#pipes-filter-sqs
        #  Check whether we need poller-specific filter-preprocessing here without modifying the actual event!
        # convert to json for filtering (HACK for fixing parity with v1 and getting regression tests passing)
        for event in polled_events:
            try:
                event["body"] = json.loads(event["body"])
            except json.JSONDecodeError:
                LOG.debug(
                    "Unable to convert event body '%s' to json... Event might be dropped.",
                    event["body"],
                )
        matching_events = self.filter_events(polled_events)
        # convert them back (HACK for fixing parity with v1 and getting regression tests passing)
        for event in matching_events:
            event["body"] = (
                json.dumps(event["body"]) if not isinstance(event["body"], str) else event["body"]
            )

        all_message_ids = {message["MessageId"] for message in messages}
        matching_message_ids = {event["messageId"] for event in matching_events}
        discarded_message_ids = all_message_ids.difference(matching_message_ids)
        # Delete discarded events immediately:
        # https://lucvandonkersgoed.com/2022/01/20/the-9-ways-an-sqs-message-can-be-deleted/#7-event-source-mappings-with-filters
        self.delete_messages(messages, discarded_message_ids)

        # Don't trigger upon empty events
        if len(matching_events) == 0:
            return
        # Enrich events with metadata after filtering
        enriched_events = self.add_source_metadata(matching_events)

        # Invoke the processor (e.g., Pipe, ESM) and handle partial batch failures
        try:
            self.processor.process_events_batch(enriched_events)
            successful_message_ids = all_message_ids
        except PartialBatchFailureError as e:
            failed_message_ids = parse_batch_item_failures(
                e.partial_failure_payload, matching_message_ids
            )
            successful_message_ids = matching_message_ids.difference(failed_message_ids)

        # Only delete messages that are processed successfully as described here:
        # https://docs.aws.amazon.com/en_gb/lambda/latest/dg/with-sqs.html
        # When Lambda reads a batch, the messages stay in the queue but are hidden for the length of the queue's
        # visibility timeout. If your function successfully processes the batch, Lambda deletes the messages
        # from the queue. By default, if your function encounters an error while processing a batch,
        # all messages in that batch become visible in the queue again. For this reason, your function code must
        # be able to process the same message multiple times without unintended side effects.
        # Troubleshooting: https://repost.aws/knowledge-center/lambda-sqs-report-batch-item-failures
        # For FIFO queues, AWS also deletes successfully sent messages. Therefore, the AWS docs recommends:
        # "If you're using this feature with a FIFO queue, your function should stop processing messages after the first
        # failure and return all failed and unprocessed messages in batchItemFailures. This helps preserve the ordering
        # of messages in your queue."
        # Following this recommendation could result in the unsolved side effect that valid messages are continuously
        # placed in the same batch as failing messages:
        # * https://stackoverflow.com/questions/78694079/how-to-stop-fifo-sqs-messages-from-being-placed-in-a-batch-with-failing-messages
        # * https://stackoverflow.com/questions/76912394/can-i-report-only-messages-from-failing-group-id-in-reportbatchitemfailures-resp

        # TODO: Test blocking failure behavior for FIFO queues to guarantee strict ordering
        #  -> might require some checkpointing or retry control on the poller side?!
        # The poller should only proceed processing FIFO queues after having retried failing messages:
        # "If your pipe returns an error, the pipe attempts all retries on the affected messages before EventBridge
        # receives additional messages from the same group."
        # https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-pipes-sqs.html
        self.delete_messages(messages, successful_message_ids)