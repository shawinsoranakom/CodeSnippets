def parse_grants_in_headers(permission: Permission, grantees: str) -> Grants:
    splitted_grantees = [grantee.strip() for grantee in grantees.split(",")]
    grants = []
    for seralized_grantee in splitted_grantees:
        grantee_type, grantee_id = seralized_grantee.split("=")
        grantee_id = grantee_id.strip('"')
        if grantee_type not in ("uri", "id", "emailAddress"):
            raise InvalidArgument(
                "Argument format not recognized",
                ArgumentName=get_permission_header_name(permission),
                ArgumentValue=seralized_grantee,
            )
        elif grantee_type == "uri":
            if grantee_id not in s3_constants.VALID_ACL_PREDEFINED_GROUPS:
                raise InvalidArgument(
                    "Invalid group uri",
                    ArgumentName="uri",
                    ArgumentValue=grantee_id,
                )
            grantee = Grantee(
                Type=GranteeType.Group,
                URI=grantee_id,
            )

        elif grantee_type == "id":
            if not is_valid_canonical_id(grantee_id):
                raise InvalidArgument(
                    "Invalid id",
                    ArgumentName="id",
                    ArgumentValue=grantee_id,
                )
            grantee = Grantee(
                Type=GranteeType.CanonicalUser,
                ID=grantee_id,
                DisplayName="webfile",  # TODO: only in certain regions
            )

        else:
            # TODO: check validation here
            grantee = Grantee(
                Type=GranteeType.AmazonCustomerByEmail,
                EmailAddress=grantee_id,
            )
        grants.append(Grant(Permission=permission, Grantee=grantee))

    return grants