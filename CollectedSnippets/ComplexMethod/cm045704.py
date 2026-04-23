def extract(self, state=None):
        from google.cloud import logging as gcp_logging

        prepared_state = json.dumps(state)
        if len(prepared_state) > MAX_GCP_ENV_VAR_LENGTH:
            raise ValueError(
                "The state is too large. Please consider using smaller number of streams."
            )

        env_overrides = []
        if state is not None:
            env_overrides.append(
                {
                    "name": "AIRBYTE_STATE",
                    "value": prepared_state,
                }
            )
        if self._cached_catalog is not None:
            env_overrides.append(
                {
                    "name": "CACHED_CATALOG",
                    "value": self._cached_catalog,
                }
            )

        operation = self.cloud_run.run_job(
            {
                "name": self.job_name,
                "overrides": {
                    "container_overrides": [
                        {
                            "name": self.config["source"]["docker_image"],
                            "env": env_overrides,
                        }
                    ]
                },
            }
        )
        execution_id = operation.metadata.name.split("/")[-1]
        execution_url = f"https://console.cloud.google.com/run/jobs/executions/details/{self.region}/{execution_id}/logs?project={self.project}"  # noqa
        logging.info(f"Launched airbyte extraction job. Details at {execution_url}")

        # Wait for execution finish
        operation_result = operation.result()
        if operation_result.succeeded_count != 1:
            raise AirbyteSourceException(
                f"GCP operation failed. Please visit {execution_url} for details."
            )

        logging.info("Execution finished, fetching results...")
        messages = None
        while messages is None:
            logging.info("Waiting for logs to be delivered in full...")
            log_client = gcp_logging.Client(
                project=self.project,
                credentials=self.credentials,
            )
            logs_processor = ConnectorResultProcessor()

            for log_entry in log_client.list_entries(
                filter_=f'labels."run.googleapis.com/execution_name" = {execution_id}',
                page_size=1000,
            ):
                logs_processor.append_chunk(log_entry.payload)

            messages = logs_processor.get_messages()
            self._cached_catalog = logs_processor.get_catalog()
            if messages is None:
                time.sleep(3.0)

        return messages