def handler(event, context):
    """Secrets Manager Rotation Template

    This is a template for creating an AWS Secrets Manager rotation lambda

    Args:
        event (dict): Lambda dictionary of event parameters. These keys must include the following:
            - SecretId: The secret ARN or identifier
            - ClientRequestToken: The ClientRequestToken of the secret version
            - Step: The rotation step (one of createSecret, setSecret, testSecret, or finishSecret)

        context (LambdaContext): The Lambda runtime information

    Raises:
        ResourceNotFoundException: If the secret with the specified arn and stage does not exist

        ValueError: If the secret is not properly configured for rotation

        KeyError: If the event parameters do not contain the expected keys

    """
    # Client setup.
    region = os.environ["AWS_REGION"]
    endpoint_url = os.environ.get("AWS_ENDPOINT_URL")

    if endpoint_url:
        verify = urlparse(endpoint_url).scheme == "https"
        service_client = boto3.client(
            "secretsmanager", endpoint_url=endpoint_url, verify=verify, region_name=region
        )
    else:
        service_client = boto3.client("secretsmanager", region_name=region)

    arn = event["SecretId"]
    token = event["ClientRequestToken"]
    step = event["Step"]

    # Make sure the version is staged correctly
    metadata = service_client.describe_secret(SecretId=arn)

    if not metadata["RotationEnabled"]:
        logger.error("Secret %s is not enabled for rotation", arn)
        raise ValueError(f"Secret {arn} is not enabled for rotation")
    #
    versions = metadata["VersionIdsToStages"]
    if token not in versions:
        logger.error("Secret version %s has no stage for rotation of secret %s.", token, arn)
        raise ValueError(f"Secret version {token} has no stage for rotation of secret {arn}.")
    if "AWSCURRENT" in versions[token]:
        logger.info("Secret version %s already set as AWSCURRENT for secret %s.", token, arn)
        return
    elif "AWSPENDING" not in versions[token]:
        logger.error(
            "Secret version %s not set as AWSPENDING for rotation of secret %s.", token, arn
        )
        raise ValueError(
            f"Secret version {token} not set as AWSPENDING for rotation of secret {arn}."
        )

    if step == "createSecret":
        create_secret(service_client, arn, token)

    elif step == "setSecret":
        set_secret(service_client, arn, token)

    elif step == "testSecret":
        test_secret(service_client, arn, token)

    elif step == "finishSecret":
        finish_secret(service_client, arn, token)

    else:
        raise ValueError("Invalid step parameter")