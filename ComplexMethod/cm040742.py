def poller_loop(self, *args, **kwargs):
        with self._state_lock:
            self.current_state = EsmState.ENABLED
            self.update_esm_state_in_store(EsmState.ENABLED)
            self.state_transition_reason = self.user_state_reason

        error_boff = ExponentialBackoff(
            initial_interval=2, max_interval=LAMBDA_EVENT_SOURCE_MAPPING_MAX_BACKOFF_ON_ERROR_SEC
        )
        empty_boff = ExponentialBackoff(
            initial_interval=1,
            max_interval=LAMBDA_EVENT_SOURCE_MAPPING_MAX_BACKOFF_ON_EMPTY_POLL_SEC,
        )

        poll_interval_duration = LAMBDA_EVENT_SOURCE_MAPPING_POLL_INTERVAL_SEC

        while not self._shutdown_event.is_set():
            try:
                # TODO: update state transition reason?
                self.poller.poll_events()

                # If no exception encountered, reset the backoff
                error_boff.reset()
                empty_boff.reset()

                # Set the poll frequency back to the default
                poll_interval_duration = LAMBDA_EVENT_SOURCE_MAPPING_POLL_INTERVAL_SEC
            except EmptyPollResultsException as miss_ex:
                # If the event source is empty, backoff
                poll_interval_duration = empty_boff.next_backoff()
                LOG.debug(
                    "The event source %s is empty. Backing off for %.2f seconds until next request.",
                    miss_ex.source_arn,
                    poll_interval_duration,
                )
            except Exception as e:
                LOG.error(
                    "Error while polling messages for event source %s: %s",
                    self.esm_config.get("EventSourceArn")
                    or self.esm_config.get("SelfManagedEventSource"),
                    e,
                    exc_info=LOG.isEnabledFor(logging.DEBUG),
                )
                event_source = parse_arn(self.esm_config.get("EventSourceArn")).get("service")
                esm_counter.labels(
                    source=event_source, status=EsmExecutionStatus.source_poller_error
                ).increment()
                # Wait some time between retries to avoid running into the problem right again
                poll_interval_duration = error_boff.next_backoff()
            finally:
                self._shutdown_event.wait(poll_interval_duration)

        # Optionally closes internal components of Poller. This is a no-op for unimplemented pollers.
        self.poller.close()

        try:
            # Update state in store after async stop or delete
            if self.enabled and self.current_state == EsmState.DELETING:
                # TODO: we also need to remove the ESM worker reference from the Lambda provider to esm_worker
                # TODO: proper locking for store updates
                self.delete_esm_in_store()
            elif not self.enabled and self.current_state == EsmState.DISABLING:
                with self._state_lock:
                    self.current_state = EsmState.DISABLED
                    self.state_transition_reason = self.user_state_reason
                self.update_esm_state_in_store(EsmState.DISABLED)
            elif not self._graceful_shutdown_triggered:
                # HACK: If we reach this state and a graceful shutdown was not triggered, log a warning to indicate
                # an unexpected state.
                LOG.warning(
                    "Invalid state %s for event source mapping %s.",
                    self.current_state,
                    self.esm_config["UUID"],
                )
        except Exception as e:
            LOG.warning(
                "Failed to update state %s for event source mapping %s. Exception: %s ",
                self.current_state,
                self.esm_config["UUID"],
                e,
                exc_info=LOG.isEnabledFor(logging.DEBUG),
            )