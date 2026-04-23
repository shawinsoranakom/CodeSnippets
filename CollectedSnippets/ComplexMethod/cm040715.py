def check_service_resource_exists(
        self, service: str, resource_arn: str, function_arn: str, function_role_arn: str
    ):
        """
        Check if the service resource exists and if the function has access to it.

        Raises:
            InvalidParameterValueException: If the service resource does not exist or the function does not have access to it.
        """
        arn = parse_arn(resource_arn)
        source_client = get_internal_client(
            arn=resource_arn,
            role_arn=function_role_arn,
            service_principal=ServicePrincipal.lambda_,
            source_arn=function_arn,
        )
        if service in ["sqs", "sqs-fifo"]:
            try:
                # AWS uses `GetQueueAttributes` internally to verify the queue existence, but we need the `QueueUrl`
                # which is not given directly. We build out a dummy `QueueUrl` which can be parsed by SQS to return
                # the right value
                queue_name = arn["resource"].split("/")[-1]
                queue_url = f"http://sqs.{arn['region']}.domain/{arn['account']}/{queue_name}"
                source_client.get_queue_attributes(QueueUrl=queue_url)
            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                if error_code == "AWS.SimpleQueueService.NonExistentQueue":
                    raise InvalidParameterValueException(
                        f"Error occurred while ReceiveMessage. SQS Error Code: {error_code}. SQS Error Message: {e.response['Error']['Message']}",
                        Type="User",
                    )
                raise e
        elif service in ["kinesis"]:
            try:
                source_client.describe_stream(StreamARN=resource_arn)
            except ClientError as e:
                if e.response["Error"]["Code"] == "ResourceNotFoundException":
                    raise InvalidParameterValueException(
                        f"Stream not found: {resource_arn}",
                        Type="User",
                    )
                raise e
        elif service in ["dynamodb"]:
            try:
                source_client.describe_stream(StreamArn=resource_arn)
            except ClientError as e:
                if e.response["Error"]["Code"] == "ResourceNotFoundException":
                    raise InvalidParameterValueException(
                        f"Stream not found: {resource_arn}",
                        Type="User",
                    )
                raise e