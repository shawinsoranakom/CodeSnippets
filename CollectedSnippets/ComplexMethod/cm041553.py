def test_kinesis_firehose_http(
    aws_client,
    lambda_processor_enabled: bool,
    create_lambda_function,
    httpserver: HTTPServer,
    cleanups,
):
    httpserver.expect_request("").respond_with_data(b"", 200)
    http_endpoint = httpserver.url_for("/")
    if lambda_processor_enabled:
        # create processor func
        func_name = f"proc-{short_uid()}"
        func_arn = create_lambda_function(handler_file=PROCESSOR_LAMBDA, func_name=func_name)[
            "CreateFunctionResponse"
        ]["FunctionArn"]

    # define firehose configs
    http_destination_update = {
        "EndpointConfiguration": {"Url": http_endpoint, "Name": "test_update"}
    }
    http_destination = {
        "EndpointConfiguration": {"Url": http_endpoint},
        "S3BackupMode": "FailedDataOnly",
        "S3Configuration": {
            "RoleARN": "arn:.*",
            "BucketARN": "arn:.*",
            "Prefix": "",
            "ErrorOutputPrefix": "",
            "BufferingHints": {"SizeInMBs": 1, "IntervalInSeconds": 60},
        },
    }

    if lambda_processor_enabled:
        http_destination["ProcessingConfiguration"] = {
            "Enabled": True,
            "Processors": [
                {
                    "Type": "Lambda",
                    "Parameters": [
                        {
                            "ParameterName": "LambdaArn",
                            "ParameterValue": func_arn,
                        }
                    ],
                }
            ],
        }

    # create firehose stream with http destination
    firehose = aws_client.firehose
    stream_name = "firehose_" + short_uid()
    stream = firehose.create_delivery_stream(
        DeliveryStreamName=stream_name,
        HttpEndpointDestinationConfiguration=http_destination,
    )
    assert stream
    cleanups.append(lambda: firehose.delete_delivery_stream(DeliveryStreamName=stream_name))

    stream_description = firehose.describe_delivery_stream(DeliveryStreamName=stream_name)
    stream_description = stream_description["DeliveryStreamDescription"]
    destination_description = stream_description["Destinations"][0][
        "HttpEndpointDestinationDescription"
    ]
    assert len(stream_description["Destinations"]) == 1
    assert destination_description["EndpointConfiguration"]["Url"] == http_endpoint

    # put record
    msg_text = "Hello World!"
    firehose.put_record(DeliveryStreamName=stream_name, Record={"Data": msg_text})

    # wait for the result to arrive with proper content
    assert poll_condition(lambda: len(httpserver.log) >= 1, timeout=5)
    request, _ = httpserver.log[0]
    record = request.get_json(force=True)
    received_record = record["records"][0]
    received_record_data = to_str(base64.b64decode(to_bytes(received_record["data"])))
    assert received_record_data == f"{msg_text}{'-processed' if lambda_processor_enabled else ''}"

    # update stream destination
    destination_id = stream_description["Destinations"][0]["DestinationId"]
    version_id = stream_description["VersionId"]
    firehose.update_destination(
        DeliveryStreamName=stream_name,
        DestinationId=destination_id,
        CurrentDeliveryStreamVersionId=version_id,
        HttpEndpointDestinationUpdate=http_destination_update,
    )
    stream_description = firehose.describe_delivery_stream(DeliveryStreamName=stream_name)
    stream_description = stream_description["DeliveryStreamDescription"]
    destination_description = stream_description["Destinations"][0][
        "HttpEndpointDestinationDescription"
    ]
    assert destination_description["EndpointConfiguration"]["Name"] == "test_update"