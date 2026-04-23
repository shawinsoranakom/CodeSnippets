def create_role(aws_client):
    role_names = []

    def _create_role(iam_client=None, **kwargs):
        if not kwargs.get("RoleName"):
            kwargs["RoleName"] = f"role-{short_uid()}"
        iam_client = iam_client or aws_client.iam
        result = iam_client.create_role(**kwargs)
        role_names.append((result["Role"]["RoleName"], iam_client))
        return result

    yield _create_role

    for role_name, iam_client in role_names:
        # detach policies
        try:
            attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)[
                "AttachedPolicies"
            ]
        except ClientError as e:
            LOG.debug(
                "Cannot list attached role policies: %s. Role %s probably already deleted...",
                e,
                role_name,
            )
            continue
        for attached_policy in attached_policies:
            try:
                iam_client.detach_role_policy(
                    RoleName=role_name, PolicyArn=attached_policy["PolicyArn"]
                )
            except Exception:
                LOG.debug(
                    "Could not detach role policy '%s' from '%s' during cleanup",
                    attached_policy["PolicyArn"],
                    role_name,
                )
        role_policies = iam_client.list_role_policies(RoleName=role_name)["PolicyNames"]
        for role_policy in role_policies:
            try:
                iam_client.delete_role_policy(RoleName=role_name, PolicyName=role_policy)
            except Exception:
                LOG.debug(
                    "Could not delete role policy '%s' from '%s' during cleanup",
                    role_policy,
                    role_name,
                )
        try:
            iam_client.delete_role(RoleName=role_name)
        except Exception:
            LOG.debug("Could not delete role '%s' during cleanup", role_name)