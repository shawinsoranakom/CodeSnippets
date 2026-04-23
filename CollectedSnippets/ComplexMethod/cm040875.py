def validate_acl_acp(acp: AccessControlPolicy) -> None:
    if acp is None or "Owner" not in acp or "Grants" not in acp:
        raise MalformedACLError(
            "The XML you provided was not well-formed or did not validate against our published schema"
        )

    if not is_valid_canonical_id(owner_id := acp["Owner"].get("ID", "")):
        raise InvalidArgument(
            "Invalid id",
            ArgumentName="CanonicalUser/ID",
            ArgumentValue=owner_id,
        )

    for grant in acp["Grants"]:
        if grant.get("Permission") not in s3_constants.VALID_GRANTEE_PERMISSIONS:
            raise MalformedACLError(
                "The XML you provided was not well-formed or did not validate against our published schema"
            )

        grantee = grant.get("Grantee", {})
        grant_type = grantee.get("Type")
        if grant_type not in (
            GranteeType.Group,
            GranteeType.CanonicalUser,
            GranteeType.AmazonCustomerByEmail,
        ):
            raise MalformedACLError(
                "The XML you provided was not well-formed or did not validate against our published schema"
            )
        elif (
            grant_type == GranteeType.Group
            and (grant_uri := grantee.get("URI", ""))
            not in s3_constants.VALID_ACL_PREDEFINED_GROUPS
        ):
            raise InvalidArgument(
                "Invalid group uri",
                ArgumentName="Group/URI",
                ArgumentValue=grant_uri,
            )

        elif grant_type == GranteeType.AmazonCustomerByEmail:
            # TODO: add validation here
            continue

        elif grant_type == GranteeType.CanonicalUser and not is_valid_canonical_id(
            grantee_id := grantee.get("ID", "")
        ):
            raise InvalidArgument(
                "Invalid id",
                ArgumentName="CanonicalUser/ID",
                ArgumentValue=grantee_id,
            )