def backend_rotate_secret(
    _,
    self,
    secret_id,
    client_request_token=None,
    rotation_lambda_arn=None,
    rotation_rules=None,
    rotate_immediately=True,
):
    rotation_days = "AutomaticallyAfterDays"

    if not self._is_valid_identifier(secret_id):
        raise SecretNotFoundException()

    secret = self.secrets[secret_id]
    if secret.is_deleted():
        raise InvalidRequestException(
            "An error occurred (InvalidRequestException) when calling the RotateSecret operation: You tried to \
            perform the operation on a secret that's currently marked deleted."
        )
    # Resolve rotation_lambda_arn and fallback to previous value if its missing
    # from the current request
    rotation_lambda_arn = rotation_lambda_arn or secret.rotation_lambda_arn
    if not rotation_lambda_arn:
        raise InvalidRequestException(
            "No Lambda rotation function ARN is associated with this secret."
        )

    if rotation_lambda_arn:
        if len(rotation_lambda_arn) > 2048:
            msg = "RotationLambdaARN must <= 2048 characters long."
            raise InvalidParameterException(msg)

    # In case rotation_period is not provided, resolve auto_rotate_after_days
    # and fallback to previous value if its missing from the current request.
    rotation_period = secret.auto_rotate_after_days or 0
    if rotation_rules:
        if rotation_days in rotation_rules:
            rotation_period = rotation_rules[rotation_days]
            if rotation_period < 1 or rotation_period > 1000:
                msg = "RotationRules.AutomaticallyAfterDays must be within 1-1000."
                raise InvalidParameterException(msg)

    try:
        lm_client = connect_to(region_name=self.region_name).lambda_
        lm_client.get_function(FunctionName=rotation_lambda_arn)
    except Exception:
        raise ResourceNotFoundException("Lambda does not exist or could not be accessed")

    # The rotation function must end with the versions of the secret in
    # one of two states:
    #
    #  - The AWSPENDING and AWSCURRENT staging labels are attached to the
    #    same version of the secret, or
    #  - The AWSPENDING staging label is not attached to any version of the secret.
    #
    # If the AWSPENDING staging label is present but not attached to the same
    # version as AWSCURRENT then any later invocation of RotateSecret assumes
    # that a previous rotation request is still in progress and returns an error.
    try:
        pending_version = None
        version = next(
            version
            for version in secret.versions.values()
            if AWSPENDING in version["version_stages"]
        )
        if AWSCURRENT not in version["version_stages"]:
            msg = "Previous rotation request is still in progress."
            # Delay exception, so we can trigger lambda again
            pending_version = [InvalidRequestException(msg), version]

    except StopIteration:
        # Pending is not present in any version
        pass

    secret.rotation_lambda_arn = rotation_lambda_arn
    secret.auto_rotate_after_days = rotation_period
    if secret.auto_rotate_after_days > 0:
        wait_interval_s = int(rotation_period) * 86400
        secret.next_rotation_date = int(time.time()) + wait_interval_s
        secret.rotation_enabled = True
        secret.rotation_requested = True

    if rotate_immediately:
        if not pending_version:
            # Begin the rotation process for the given secret by invoking the lambda function.
            #
            # We add the new secret version as "pending". The previous version remains
            # as "current" for now. Once we've passed the new secret through the lambda
            # rotation function (if provided) we can then update the status to "current".
            new_version_id = self._from_client_request_token(client_request_token)

            # An initial dummy secret value is necessary otherwise moto is not adding the new
            # secret version.
            self._add_secret(
                secret_id,
                "dummy_password",
                description=secret.description,
                tags=secret.tags,
                version_id=new_version_id,
                version_stages=[AWSPENDING],
            )

            # AWS secret rotation function templates have checks on existing values so we remove
            # the dummy value to force the lambda to generate a new one.
            del secret.versions[new_version_id]["secret_string"]
        else:
            new_version_id = pending_version.pop()["version_id"]

        try:
            for step in ["create", "set", "test", "finish"]:
                resp = lm_client.invoke(
                    FunctionName=rotation_lambda_arn,
                    Payload=json.dumps(
                        {
                            "Step": step + "Secret",
                            "SecretId": secret.name,
                            "ClientRequestToken": new_version_id,
                        }
                    ),
                )
                if resp.get("FunctionError"):
                    data = json.loads(resp.get("Payload").read())
                    raise Exception(data.get("errorType"))
        except Exception as e:
            LOG.debug("An exception (%s) has occurred in %s", str(e), rotation_lambda_arn)
            if pending_version:
                raise pending_version.pop()
            # Fall through if there is no previously pending version so we'll "stuck" with a new
            # secret version in AWSPENDING state.
    secret.last_rotation_date = int(time.time())
    return secret.to_short_dict(version_id=new_version_id)