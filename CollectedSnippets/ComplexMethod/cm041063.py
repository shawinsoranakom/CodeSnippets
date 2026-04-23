def resolve_refs_recursively(
    account_id: str,
    region_name: str,
    stack_name: str,
    resources: dict,
    mappings: dict,
    conditions: dict[str, bool],
    parameters: dict,
    value,
):
    result = _resolve_refs_recursively(
        account_id, region_name, stack_name, resources, mappings, conditions, parameters, value
    )

    # localstack specific patches
    if isinstance(result, str):
        # we're trying to filter constructed API urls here (e.g. via Join in the template)
        api_match = REGEX_OUTPUT_APIGATEWAY.match(result)
        if api_match and result in config.CFN_STRING_REPLACEMENT_DENY_LIST:
            return result
        elif api_match:
            prefix = api_match[1]
            host = api_match[2]
            path = api_match[3]
            port = localstack_host().port
            return f"{prefix}{host}:{port}/{path}"

        # basic dynamic reference support
        # see: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/dynamic-references.html
        # technically there are more restrictions for each of these services but checking each of these
        # isn't really necessary for the current level of emulation
        dynamic_ref_match = REGEX_DYNAMIC_REF.match(result)
        if dynamic_ref_match:
            service_name = dynamic_ref_match[1]
            reference_key = dynamic_ref_match[2]

            # only these 3 services are supported for dynamic references right now
            if service_name == "ssm":
                ssm_client = connect_to(aws_access_key_id=account_id, region_name=region_name).ssm
                try:
                    return ssm_client.get_parameter(Name=reference_key)["Parameter"]["Value"]
                except ClientError as e:
                    LOG.error("client error accessing SSM parameter '%s': %s", reference_key, e)
                    raise
            elif service_name == "ssm-secure":
                ssm_client = connect_to(aws_access_key_id=account_id, region_name=region_name).ssm
                try:
                    return ssm_client.get_parameter(Name=reference_key, WithDecryption=True)[
                        "Parameter"
                    ]["Value"]
                except ClientError as e:
                    LOG.error("client error accessing SSM parameter '%s': %s", reference_key, e)
                    raise
            elif service_name == "secretsmanager":
                # reference key needs to be parsed further
                # because {{resolve:secretsmanager:secret-id:secret-string:json-key:version-stage:version-id}}
                # we match for "secret-id:secret-string:json-key:version-stage:version-id"
                # where
                #   secret-id can either be the secret name or the full ARN of the secret
                #   secret-string *must* be SecretString
                #   all other values are optional
                secret_id = reference_key
                [json_key, version_stage, version_id] = [None, None, None]
                if "SecretString" in reference_key:
                    parts = reference_key.split(":SecretString:")
                    secret_id = parts[0]
                    # json-key, version-stage and version-id are optional.
                    [json_key, version_stage, version_id] = f"{parts[1]}::".split(":")[:3]

                kwargs = {}  # optional args for get_secret_value
                if version_id:
                    kwargs["VersionId"] = version_id
                if version_stage:
                    kwargs["VersionStage"] = version_stage

                secretsmanager_client = connect_to(
                    aws_access_key_id=account_id, region_name=region_name
                ).secretsmanager
                try:
                    secret_value = secretsmanager_client.get_secret_value(
                        SecretId=secret_id, **kwargs
                    )["SecretString"]
                except ClientError:
                    LOG.error("client error while trying to access key '%s': %s", secret_id)
                    raise

                if json_key:
                    json_secret = json.loads(secret_value)
                    if json_key not in json_secret:
                        raise DependencyNotYetSatisfied(
                            resource_ids=secret_id,
                            message=f"Key {json_key} is not yet available in secret {secret_id}.",
                        )
                    return json_secret[json_key]
                else:
                    return secret_value
            else:
                LOG.warning(
                    "Unsupported service for dynamic parameter: service_name=%s", service_name
                )

    return result