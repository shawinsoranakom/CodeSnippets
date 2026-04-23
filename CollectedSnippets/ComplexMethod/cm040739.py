def run_log_loop(self, *args, **kwargs) -> None:
        logs_client = connect_to.with_assumed_role(
            region_name=self.region,
            role_arn=self.role_arn,
            service_principal=ServicePrincipal.lambda_,
        ).logs
        while not self._shutdown_event.is_set():
            log_item = self.log_queue.get()
            if log_item is QUEUE_SHUTDOWN:
                return
            # we need to split by newline - but keep the newlines in the strings
            # strips empty lines, as they are not accepted by cloudwatch
            logs = [line + "\n" for line in log_item.logs.split("\n") if line]
            # until we have a better way to have timestamps, log events have the same time for a single invocation
            log_events = [
                {"timestamp": int(time.time() * 1000), "message": log_line} for log_line in logs
            ]
            try:
                try:
                    logs_client.put_log_events(
                        logGroupName=log_item.log_group,
                        logStreamName=log_item.log_stream,
                        logEvents=log_events,
                    )
                except logs_client.exceptions.ResourceNotFoundException:
                    # create new log group
                    try:
                        logs_client.create_log_group(logGroupName=log_item.log_group)
                    except logs_client.exceptions.ResourceAlreadyExistsException:
                        pass
                    logs_client.create_log_stream(
                        logGroupName=log_item.log_group, logStreamName=log_item.log_stream
                    )
                    logs_client.put_log_events(
                        logGroupName=log_item.log_group,
                        logStreamName=log_item.log_stream,
                        logEvents=log_events,
                    )
            except Exception as e:
                LOG.warning(
                    "Error saving logs to group %s in region %s: %s",
                    log_item.log_group,
                    self.region,
                    e,
                )