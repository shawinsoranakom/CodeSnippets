def forward_events_to_target(self, shard_id, records):
        polled_events = self.transform_into_events(records, shard_id)
        abort_condition = None
        # TODO: implement format detection behavior (e.g., for JSON body):
        #  https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-pipes-event-filtering.html
        #  Check whether we need poller-specific filter-preprocessing here without modifying the actual event!
        # convert to json for filtering (HACK for fixing parity with v1 and getting regression tests passing)
        # localstack.services.lambda_.event_source_listeners.kinesis_event_source_listener.KinesisEventSourceListener._filter_records
        # TODO: explore better abstraction for the entire filtering, including the set_data and get_data remapping
        #  We need better clarify which transformations happen before and after filtering -> fix missing test coverage
        parsed_events = self.pre_filter(polled_events)
        # TODO: advance iterator past matching events!
        #  We need to checkpoint the sequence number for each shard and then advance the shard iterator using
        #  GetShardIterator with a given sequence number
        #  https://docs.aws.amazon.com/kinesis/latest/APIReference/API_GetShardIterator.html
        #  Failing to do so kinda blocks the stream resulting in very high latency.
        matching_events = self.filter_events(parsed_events)
        matching_events_post_filter = self.post_filter(matching_events)

        # TODO: implement MaximumBatchingWindowInSeconds flush condition (before or after filter?)
        # Don't trigger upon empty events
        if len(matching_events_post_filter) == 0:
            return

        events = self.add_source_metadata(matching_events_post_filter)
        LOG.debug("Polled %d events from %s in shard %s", len(events), self.source_arn, shard_id)
        #  -> This could be tested by setting a high retry number, using a long pipe execution, and a relatively
        #  short record expiration age at the source. Check what happens if the record expires at the source.
        #  A potential implementation could use checkpointing based on the iterator position (within shard scope)
        # TODO: handle partial batch failure (see poller.py:parse_batch_item_failures)
        # TODO: think about how to avoid starvation of other shards if one shard runs into infinite retries
        attempts = 0
        discarded_events_for_dlq = []
        error_payload = {}

        max_retries = self.stream_parameters.get("MaximumRetryAttempts", -1)
        max_record_age = max(
            self.stream_parameters.get("MaximumRecordAgeInSeconds", -1), 0
        )  # Disable check if -1
        # NOTE: max_retries == 0 means exponential backoff is disabled
        boff = ExponentialBackoff(max_retries=max_retries)
        while not abort_condition and events and not self._is_shutdown.is_set():
            if self.max_retries_exceeded(attempts):
                abort_condition = "RetryAttemptsExhausted"
                break

            if max_record_age:
                events, expired_events = self.bisect_events_by_record_age(max_record_age, events)
                if expired_events:
                    discarded_events_for_dlq.extend(expired_events)
                    continue

            try:
                if attempts > 0:
                    # TODO: Should we always backoff (with jitter) before processing since we may not want multiple pollers
                    # all starting up and polling simultaneously
                    # For example: 500 persisted ESMs starting up and requesting concurrently could flood gateway
                    self._is_shutdown.wait(boff.next_backoff())

                self.processor.process_events_batch(events)
                boff.reset()
                # We may need to send on data to a DLQ so break the processing loop and proceed if invocation successful.
                break
            except PartialBatchFailureError as ex:
                # TODO: add tests for partial batch failure scenarios
                if (
                    self.stream_parameters.get("OnPartialBatchItemFailure")
                    == OnPartialBatchItemFailureStreams.AUTOMATIC_BISECT
                ):
                    # TODO: implement and test splitting batches in half until batch size 1
                    #  https://docs.aws.amazon.com/eventbridge/latest/pipes-reference/API_PipeSourceKinesisStreamParameters.html
                    LOG.warning(
                        "AUTOMATIC_BISECT upon partial batch item failure is not yet implemented. Retrying the entire batch."
                    )
                error_payload = ex.error

                # Extract all sequence numbers from events in batch. This allows us to fail the whole batch if
                # an unknown itemidentifier is returned.
                batch_sequence_numbers = {
                    self.get_sequence_number(event) for event in matching_events
                }

                # If the batchItemFailures array contains multiple items, Lambda uses the record with the lowest sequence number as the checkpoint.
                # Lambda then retries all records starting from that checkpoint.
                failed_sequence_ids: list[int] | None = get_batch_item_failures(
                    ex.partial_failure_payload, batch_sequence_numbers
                )

                # If None is returned, consider the entire batch a failure.
                if failed_sequence_ids is None:
                    continue

                # This shouldn't be possible since a PartialBatchFailureError was raised
                if len(failed_sequence_ids) == 0:
                    assert failed_sequence_ids, (
                        "Invalid state encountered: PartialBatchFailureError raised but no batch item failures found."
                    )

                lowest_sequence_id: str = min(failed_sequence_ids, key=int)

                # Discard all successful events and re-process from sequence number of failed event
                _, events = self.bisect_events(lowest_sequence_id, events)
            except BatchFailureError as ex:
                error_payload = ex.error

                # FIXME partner_resource_arn is not defined in ESM
                LOG.debug(
                    "Attempt %d failed while processing %s with events: %s",
                    attempts,
                    self.partner_resource_arn or self.source_arn,
                    events,
                    exc_info=LOG.isEnabledFor(logging.DEBUG),
                )
            except Exception:
                # FIXME partner_resource_arn is not defined in ESM
                LOG.error(
                    "Attempt %d failed with unexpected error while processing %s with events: %s",
                    attempts,
                    self.partner_resource_arn or self.source_arn,
                    events,
                    exc_info=LOG.isEnabledFor(logging.DEBUG),
                )
            finally:
                # Retry polling until the record expires at the source
                attempts += 1

        if discarded_events_for_dlq:
            abort_condition = "RecordAgeExceeded"
            error_payload = {}
            events = discarded_events_for_dlq

        # Send failed events to potential DLQ
        if abort_condition:
            failure_context = self.processor.generate_event_failure_context(
                abort_condition=abort_condition,
                error=error_payload,
                attempts_count=attempts,
                partner_resource_arn=self.partner_resource_arn,
            )
            self.send_events_to_dlq(shard_id, events, context=failure_context)