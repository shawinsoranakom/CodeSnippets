def moto_put_subscription_filter(fn, self, *args, **kwargs):
    log_group_name = args[0]
    filter_name = args[1]
    filter_pattern = args[2]
    destination_arn = args[3]
    role_arn = args[4]

    log_group = self.groups.get(log_group_name)
    log_group_arn = arns.log_group_arn(log_group_name, self.account_id, self.region_name)

    if not log_group:
        raise ResourceNotFoundException("The specified log group does not exist.")

    arn_data = arns.parse_arn(destination_arn)

    if role_arn:
        factory = connect_to.with_assumed_role(
            role_arn=role_arn,
            service_principal=ServicePrincipal.logs,
            region_name=arn_data["region"],
        )
    else:
        factory = connect_to(aws_access_key_id=arn_data["account"], region_name=arn_data["region"])

    if ":lambda:" in destination_arn:
        client = factory.lambda_.request_metadata(
            source_arn=log_group_arn, service_principal=ServicePrincipal.logs
        )
        try:
            client.get_function(FunctionName=destination_arn)
        except Exception:
            raise InvalidParameterException(
                "destinationArn for vendor lambda cannot be used with roleArn"
            )

    elif ":kinesis:" in destination_arn:
        client = factory.kinesis.request_metadata(
            source_arn=log_group_arn, service_principal=ServicePrincipal.logs
        )
        stream_name = arns.kinesis_stream_name(destination_arn)
        try:
            # Kinesis-Local DescribeStream does not support StreamArn param, so use StreamName instead
            client.describe_stream(StreamName=stream_name)
        except Exception:
            raise InvalidParameterException(
                "Could not deliver message to specified Kinesis stream. "
                "Ensure that the Kinesis stream exists and is ACTIVE."
            )

    elif ":firehose:" in destination_arn:
        client = factory.firehose.request_metadata(
            source_arn=log_group_arn, service_principal=ServicePrincipal.logs
        )
        firehose_name = arns.firehose_name(destination_arn)
        try:
            client.describe_delivery_stream(DeliveryStreamName=firehose_name)
        except Exception:
            raise InvalidParameterException(
                "Could not deliver message to specified Firehose stream. "
                "Ensure that the Firehose stream exists and is ACTIVE."
            )

    else:
        raise InvalidParameterException(
            f"PutSubscriptionFilter operation cannot work with destinationArn for vendor {arn_data['service']}"
        )

    if filter_pattern:
        for stream in log_group.streams.values():
            stream.filter_pattern = filter_pattern

    log_group.put_subscription_filter(filter_name, filter_pattern, destination_arn, role_arn)