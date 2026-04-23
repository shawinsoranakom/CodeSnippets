def _run(self, decoded_tokens: list[int], complete_transfers: bool):
        """
        Runs multiple engine (scheduler + worker) steps.
        Assumes a single request is running.

        Args:
            decoded_tokens: the tokens to yield at each step.
            complete_transfers: complete transfers immediately
        """

        tokens_iter = iter(decoded_tokens)
        token_id = next(tokens_iter, None)
        prev_scheduler_output = None
        prev_model_runner_output = None
        while True:
            assert self.scheduler.requests

            scheduler_output = self.scheduler.schedule()
            self._update_gpu_block_idx()

            kv_connector_metadata = scheduler_output.kv_connector_metadata
            assert kv_connector_metadata is not None
            assert isinstance(kv_connector_metadata, OffloadingConnectorMetadata)

            self.worker_connector.handle_preemptions(kv_connector_metadata)

            self.worker_connector.bind_connector_metadata(kv_connector_metadata)
            self.worker_connector.start_load_kv(self._dummy_ctx)

            if scheduler_output.total_num_scheduled_tokens > 0:
                self.worker_connector.wait_for_save()

            if complete_transfers:
                self.offloading_spec.complete_transfers()

            finished_sending, finished_recving = self.worker_connector.get_finished(
                scheduler_output.finished_req_ids
            )

            self.worker_connector.clear_connector_metadata()

            model_runner_output = create_model_runner_output(
                reqs=self.scheduler.running,
                finished_sending=finished_sending,
                finished_recving=finished_recving,
                token_id=token_id or 0,
            )

            prev_token_id = token_id
            if self.scheduler.running:
                token_id = next(tokens_iter, None)

            if self.async_scheduling:
                # in async scheduling we update the output of the previous step
                if prev_model_runner_output is not None:
                    self.scheduler.update_from_output(
                        prev_scheduler_output, prev_model_runner_output
                    )
                prev_scheduler_output = scheduler_output
                prev_model_runner_output = model_runner_output
            else:
                self.scheduler.update_from_output(scheduler_output, model_runner_output)

            if (
                prev_token_id == EOS_TOKEN_ID
                and prev_token_id != token_id
                and self.scheduler.requests
            ):
                # continue for one more step to allow offloading to kick off
                continue

            if token_id is None:
                if self.async_scheduling:
                    # sample last token
                    self.scheduler.update_from_output(
                        prev_scheduler_output, prev_model_runner_output
                    )
                break

        self._parse_transfers()

        # run one more step to update finished stored
        if EOS_TOKEN_ID in decoded_tokens:
            assert not self.scheduler.running

            while self.scheduler.requests:
                scheduler_output = self.scheduler.schedule()

                finished_sending, finished_recving = self.worker_connector.get_finished(
                    scheduler_output.finished_req_ids
                )

                assert not finished_recving

                model_runner_output = copy.deepcopy(EMPTY_MODEL_RUNNER_OUTPUT)
                model_runner_output.kv_connector_output = KVConnectorOutput(
                    finished_sending=finished_sending
                )

                self.scheduler.update_from_output(scheduler_output, model_runner_output)