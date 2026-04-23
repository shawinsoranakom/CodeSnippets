def extract_log_arn_parts_from(
        logging_configuration: LoggingConfiguration,
    ) -> tuple[str, str, str] | None:
        # Returns a tuple with: account_id, region, and log group name if the logging configuration
        # specifies a valid cloud watch log group arn, none otherwise.

        destinations = logging_configuration.get("destinations")
        if not destinations or len(destinations) > 1:  # Only one destination can be defined.
            return None

        log_group = destinations[0].get("cloudWatchLogsLogGroup")
        if not log_group:
            return None

        log_group_arn = log_group.get("logGroupArn")
        if not log_group_arn:
            return None

        try:
            arn_data: ArnData = parse_arn(log_group_arn)
        except InvalidArnException:
            return None

        log_region = arn_data.get("region")
        if log_region is None:
            return None

        log_account_id = arn_data.get("account")
        if log_account_id is None:
            return None

        log_resource = arn_data.get("resource")
        if log_resource is None:
            return None

        log_resource_parts = log_resource.split("log-group:")
        if not log_resource_parts:
            return None

        log_group_name = log_resource_parts[-1].split(":")[0]
        return log_account_id, log_region, log_group_name