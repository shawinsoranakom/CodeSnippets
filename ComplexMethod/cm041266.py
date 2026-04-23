def create_lambda_function(
    func_name,
    zip_file=None,
    event_source_arn=None,
    handler_file=None,
    handler=None,
    starting_position=None,
    runtime=None,
    envvars=None,
    tags=None,
    libs=None,
    delete=False,
    layers=None,
    client=None,
    role=None,
    timeout=None,
    region_name=None,
    s3_client=None,
    **kwargs,
):
    """Utility method to create a new function via the Lambda API
    CAVEAT: Does NOT wait until the function is ready/active. The fixture create_lambda_function waits until ready.
    """
    if envvars is None:
        envvars = {}
    if tags is None:
        tags = {}
    if libs is None:
        libs = []

    starting_position = starting_position or LAMBDA_DEFAULT_STARTING_POSITION
    runtime = runtime or LAMBDA_DEFAULT_RUNTIME
    client = client or connect_to(region_name=region_name).lambda_

    # load zip file content if handler_file is specified
    if not zip_file and handler_file:
        file_content = load_file(handler_file) if os.path.exists(handler_file) else handler_file
        if libs or not handler:
            zip_file = create_lambda_archive(
                file_content,
                libs=libs,
                get_content=True,
                runtime=runtime or LAMBDA_DEFAULT_RUNTIME,
            )
        else:
            zip_file = create_zip_file(handler_file, get_content=True)

    handler = handler or LAMBDA_DEFAULT_HANDLER

    if delete:
        try:
            # Delete function if one already exists
            client.delete_function(FunctionName=func_name)
        except Exception:
            pass

    lambda_code = {"ZipFile": zip_file}
    if len(zip_file) > MAX_LAMBDA_ARCHIVE_UPLOAD_SIZE:
        s3 = s3_client or connect_externally_to().s3
        resource_utils.get_or_create_bucket(LAMBDA_ASSETS_BUCKET_NAME)
        asset_key = f"{short_uid()}.zip"
        s3.upload_fileobj(
            Fileobj=io.BytesIO(zip_file), Bucket=LAMBDA_ASSETS_BUCKET_NAME, Key=asset_key
        )
        lambda_code = {"S3Bucket": LAMBDA_ASSETS_BUCKET_NAME, "S3Key": asset_key}

    # create function
    additional_kwargs = kwargs
    kwargs = {
        "FunctionName": func_name,
        "Runtime": runtime,
        "Handler": handler,
        "Role": role or LAMBDA_TEST_ROLE.format(account_id=TEST_AWS_ACCOUNT_ID),
        "Code": lambda_code,
        "Timeout": timeout or LAMBDA_TIMEOUT_SEC,
        "Environment": {"Variables": envvars},
        "Tags": tags,
    }
    kwargs.update(additional_kwargs)
    if layers:
        kwargs["Layers"] = layers
    create_func_resp = client.create_function(**kwargs)

    resp = {
        "CreateFunctionResponse": create_func_resp,
        "CreateEventSourceMappingResponse": None,
    }

    # create event source mapping
    if event_source_arn:
        resp["CreateEventSourceMappingResponse"] = client.create_event_source_mapping(
            FunctionName=func_name,
            EventSourceArn=event_source_arn,
            StartingPosition=starting_position,
        )

    return resp