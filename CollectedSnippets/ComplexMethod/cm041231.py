def create_user(aws_client):
    usernames = []

    def _create_user(**kwargs):
        if "UserName" not in kwargs:
            kwargs["UserName"] = f"user-{short_uid()}"
        response = aws_client.iam.create_user(**kwargs)
        usernames.append(response["User"]["UserName"])
        return response

    yield _create_user

    for username in usernames:
        try:
            inline_policies = aws_client.iam.list_user_policies(UserName=username)["PolicyNames"]
        except ClientError as e:
            LOG.debug(
                "Cannot list user policies: %s. User %s probably already deleted...", e, username
            )
            continue

        for inline_policy in inline_policies:
            try:
                aws_client.iam.delete_user_policy(UserName=username, PolicyName=inline_policy)
            except Exception:
                LOG.debug(
                    "Could not delete user policy '%s' from '%s' during cleanup",
                    inline_policy,
                    username,
                )
        attached_policies = aws_client.iam.list_attached_user_policies(UserName=username)[
            "AttachedPolicies"
        ]
        for attached_policy in attached_policies:
            try:
                aws_client.iam.detach_user_policy(
                    UserName=username, PolicyArn=attached_policy["PolicyArn"]
                )
            except Exception:
                LOG.debug(
                    "Error detaching policy '%s' from user '%s'",
                    attached_policy["PolicyArn"],
                    username,
                )
        access_keys = aws_client.iam.list_access_keys(UserName=username)["AccessKeyMetadata"]
        for access_key in access_keys:
            try:
                aws_client.iam.delete_access_key(
                    UserName=username, AccessKeyId=access_key["AccessKeyId"]
                )
            except Exception:
                LOG.debug(
                    "Error deleting access key '%s' from user '%s'",
                    access_key["AccessKeyId"],
                    username,
                )

        try:
            aws_client.iam.delete_user(UserName=username)
        except Exception as e:
            LOG.debug("Error deleting user '%s' during test cleanup: %s", username, e)