def test_policy_attachments(deploy_cfn_template, aws_client):
    role_name = f"role-{short_uid()}"
    group_name = f"group-{short_uid()}"
    user_name = f"user-{short_uid()}"
    policy_name = f"policy-{short_uid()}"

    linked_role_id = short_uid()
    deploy_cfn_template(
        template_path=os.path.join(
            os.path.dirname(__file__), "../../../templates/iam_policy_attachments.yaml"
        ),
        template_mapping={
            "role_name": role_name,
            "policy_name": policy_name,
            "user_name": user_name,
            "group_name": group_name,
            "service_linked_role_id": linked_role_id,
        },
    )

    # check inline policies
    role_inline_policies = aws_client.iam.list_role_policies(RoleName=role_name)
    user_inline_policies = aws_client.iam.list_user_policies(UserName=user_name)
    group_inline_policies = aws_client.iam.list_group_policies(GroupName=group_name)
    assert len(role_inline_policies["PolicyNames"]) == 2
    assert len(user_inline_policies["PolicyNames"]) == 1
    assert len(group_inline_policies["PolicyNames"]) == 1

    # check managed/attached policies
    role_attached_policies = aws_client.iam.list_attached_role_policies(RoleName=role_name)
    user_attached_policies = aws_client.iam.list_attached_user_policies(UserName=user_name)
    group_attached_policies = aws_client.iam.list_attached_group_policies(GroupName=group_name)
    assert len(role_attached_policies["AttachedPolicies"]) == 1
    assert len(user_attached_policies["AttachedPolicies"]) == 1
    assert len(group_attached_policies["AttachedPolicies"]) == 1

    # check service linked roles
    roles = aws_client.iam.list_roles(PathPrefix=SERVICE_LINKED_ROLE_PATH_PREFIX)["Roles"]
    matching = [r for r in roles if r.get("Description") == f"service linked role {linked_role_id}"]
    assert matching
    policy = matching[0]["AssumeRolePolicyDocument"]
    policy = json.loads(policy) if isinstance(policy, str) else policy
    assert policy["Statement"][0]["Principal"] == {"Service": "elasticbeanstalk.amazonaws.com"}