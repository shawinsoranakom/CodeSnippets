def get_canned_acl(
    canned_acl: BucketCannedACL | ObjectCannedACL, owner: Owner
) -> AccessControlPolicy:
    """
    Return the proper Owner and Grants from a CannedACL
    See https://docs.aws.amazon.com/AmazonS3/latest/userguide/acl-overview.html#canned-acl
    :param canned_acl: an S3 CannedACL
    :param owner: the current owner of the bucket or object
    :return: an AccessControlPolicy containing the Grants and Owner
    """
    owner_grantee = Grantee(**owner, Type=GranteeType.CanonicalUser)
    grants = [Grant(Grantee=owner_grantee, Permission=Permission.FULL_CONTROL)]

    match canned_acl:
        case ObjectCannedACL.private:
            pass  # no other permissions
        case ObjectCannedACL.public_read:
            grants.append(Grant(Grantee=ALL_USERS_ACL_GRANTEE, Permission=Permission.READ))

        case ObjectCannedACL.public_read_write:
            grants.append(Grant(Grantee=ALL_USERS_ACL_GRANTEE, Permission=Permission.READ))
            grants.append(Grant(Grantee=ALL_USERS_ACL_GRANTEE, Permission=Permission.WRITE))
        case ObjectCannedACL.authenticated_read:
            grants.append(
                Grant(Grantee=AUTHENTICATED_USERS_ACL_GRANTEE, Permission=Permission.READ)
            )
        case ObjectCannedACL.bucket_owner_read:
            pass  # TODO: bucket owner ACL
        case ObjectCannedACL.bucket_owner_full_control:
            pass  # TODO: bucket owner ACL
        case ObjectCannedACL.aws_exec_read:
            pass  # TODO: bucket owner, EC2 Read
        case BucketCannedACL.log_delivery_write:
            grants.append(Grant(Grantee=LOG_DELIVERY_ACL_GRANTEE, Permission=Permission.READ_ACP))
            grants.append(Grant(Grantee=LOG_DELIVERY_ACL_GRANTEE, Permission=Permission.WRITE))

    return AccessControlPolicy(Owner=owner, Grants=grants)