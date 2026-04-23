def validate_post_policy(
    request_form: ImmutableMultiDict, additional_policy_metadata: dict
) -> None:
    """
    Validate the pre-signed POST with its policy contained
    For now, only validates its expiration
    SigV2: https://docs.aws.amazon.com/AmazonS3/latest/userguide/HTTPPOSTExamples.html
    SigV4: https://docs.aws.amazon.com/AmazonS3/latest/API/sigv4-authentication-HTTPPOST.html

    :param request_form: the form data contained in the pre-signed POST request
    :param additional_policy_metadata: additional metadata needed to validate the policy (bucket name, object size)
    :raises AccessDenied, SignatureDoesNotMatch
    :return: None
    """
    if not request_form.get("key"):
        raise InvalidArgument(
            "Bucket POST must contain a field named 'key'.  If it is specified, please check the order of the fields.",
            ArgumentName="key",
            ArgumentValue="",
            HostId=S3_HOST_ID,
        )

    form_dict = {k.lower(): v for k, v in request_form.items()}

    policy = form_dict.get("policy")
    if not policy:
        # A POST request needs a policy except if the bucket is publicly writable
        return

    # TODO: this does validation of fields only for now
    is_v4 = _is_match_with_signature_fields(form_dict, SIGNATURE_V4_POST_FIELDS)
    is_v2 = _is_match_with_signature_fields(form_dict, SIGNATURE_V2_POST_FIELDS)

    if not is_v2 and not is_v4:
        ex: AccessDenied = AccessDenied("Access Denied")
        ex.HostId = S3_HOST_ID
        raise ex

    try:
        policy_decoded = json.loads(base64.b64decode(policy).decode("utf-8"))
    except ValueError:
        # this means the policy has been tampered with
        signature = form_dict.get("signature") if is_v2 else form_dict.get("x-amz-signature")
        credentials = get_credentials_from_parameters(request_form, "us-east-1")
        ex: SignatureDoesNotMatch = create_signature_does_not_match_sig_v2(
            request_signature=signature,
            string_to_sign=policy,
            access_key_id=credentials.access_key_id,
        )
        raise ex

    if expiration := policy_decoded.get("expiration"):
        if is_expired(_parse_policy_expiration_date(expiration)):
            ex: AccessDenied = AccessDenied("Invalid according to Policy: Policy expired.")
            ex.HostId = S3_HOST_ID
            raise ex

    # TODO: validate the signature

    # See https://docs.aws.amazon.com/AmazonS3/latest/API/sigv4-HTTPPOSTConstructPolicy.html
    # for the list of conditions and what matching they support
    # TODO:
    #  1. only support the kind of matching the field supports: `success_action_status` does not support `starts-with`
    #  matching
    #  2. if there are fields that are not defined in the policy, we should reject it

    # Special case for LEGACY_V2: do not validate the conditions. Remove this check once we remove legacy_v2
    if not additional_policy_metadata:
        return

    conditions = policy_decoded.get("conditions", [])
    for condition in conditions:
        if not _verify_condition(condition, form_dict, additional_policy_metadata):
            str_condition = str(condition).replace("'", '"')
            raise AccessDenied(
                f"Invalid according to Policy: Policy Condition failed: {str_condition}",
                HostId=S3_HOST_ID,
            )