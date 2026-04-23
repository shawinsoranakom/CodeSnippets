def get_access_control_policy_from_acl_request(
    request: PutBucketAclRequest | PutObjectAclRequest,
    owner: Owner,
    request_body: bytes,
) -> AccessControlPolicy:
    canned_acl = request.get("ACL")
    acl_headers = get_acl_headers_from_request(request)

    # FIXME: this is very dirty, but the parser does not differentiate between an empty body and an empty XML node
    # errors are different depending on that data, so we need to access the context. Modifying the parser for this
    # use case seems dangerous
    is_acp_in_body = request_body

    if not (canned_acl or acl_headers or is_acp_in_body):
        raise MissingSecurityHeader(
            "Your request was missing a required header", MissingHeaderName="x-amz-acl"
        )

    elif canned_acl and acl_headers:
        raise InvalidRequest("Specifying both Canned ACLs and Header Grants is not allowed")

    elif (canned_acl or acl_headers) and is_acp_in_body:
        raise UnexpectedContent("This request does not support content")

    if canned_acl:
        validate_canned_acl(canned_acl)
        acp = get_canned_acl(canned_acl, owner=owner)

    elif acl_headers:
        grants = []
        for permission, grantees_values in acl_headers:
            permission = get_permission_from_header(permission)
            partial_grants = parse_grants_in_headers(permission, grantees_values)
            grants.extend(partial_grants)

        acp = AccessControlPolicy(Owner=owner, Grants=grants)
    else:
        acp = request.get("AccessControlPolicy")
        validate_acl_acp(acp)
        if (
            owner.get("DisplayName")
            and acp["Grants"]
            and "DisplayName" not in acp["Grants"][0]["Grantee"]
        ):
            acp["Grants"][0]["Grantee"]["DisplayName"] = owner["DisplayName"]

    return acp