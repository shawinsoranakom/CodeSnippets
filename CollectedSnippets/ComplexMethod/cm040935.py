def get_table_stream_type(
    account_id: str, region_name: str, table_name_or_arn: str
) -> TableStreamType | None:
    """
    :param account_id: the account id of the table
    :param region_name: the region of the table
    :param table_name_or_arn: the table name or ARN
    :return: a TableStreamViewType object if the table has streams enabled. If not, return None
    """
    if not table_name_or_arn:
        return None

    table_name = table_name_or_arn.split(":table/")[-1]

    is_kinesis = False
    stream_view_type = None

    # To determine if stream to kinesis is enabled, we look for active kinesis destinations
    destinations = get_store(account_id, region_name).streaming_destinations.get(table_name) or []
    for destination in destinations:
        if destination["DestinationStatus"] == DestinationStatus.ACTIVE:
            is_kinesis = True

    table_arn = arns.dynamodb_table_arn(table_name, account_id=account_id, region_name=region_name)
    if (
        stream := dynamodbstreams_api.get_stream_for_table(account_id, region_name, table_arn)
    ) and stream["StreamStatus"] in (StreamStatus.ENABLING, StreamStatus.ENABLED):
        stream_view_type = stream["StreamViewType"]

    if is_kinesis or stream_view_type:
        return TableStreamType(stream_view_type, is_kinesis=is_kinesis)
    return None