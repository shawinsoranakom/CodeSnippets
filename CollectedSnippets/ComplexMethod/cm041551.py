def test_create_role_with_assume_role_policy(self, aws_client, account_id, create_role):
        role_name_1 = f"role-{short_uid()}"
        role_name_2 = f"role-{short_uid()}"

        assume_role_policy_doc = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {"AWS": f"arn:aws:iam::{account_id}:root"},
                }
            ],
        }
        str_assume_role_policy_doc = json.dumps(assume_role_policy_doc)

        create_role(
            Path="/",
            RoleName=role_name_1,
            AssumeRolePolicyDocument=str_assume_role_policy_doc,
        )

        roles = aws_client.iam.list_roles()["Roles"]
        for role in roles:
            if role["RoleName"] == role_name_1:
                assert role["AssumeRolePolicyDocument"] == assume_role_policy_doc

        create_role(
            Path="/",
            RoleName=role_name_2,
            AssumeRolePolicyDocument=str_assume_role_policy_doc,
            Description="string",
        )

        roles = aws_client.iam.list_roles()["Roles"]
        for role in roles:
            if role["RoleName"] in [role_name_1, role_name_2]:
                assert role["AssumeRolePolicyDocument"] == assume_role_policy_doc
                aws_client.iam.delete_role(RoleName=role["RoleName"])

        create_role(
            Path="/myPath/",
            RoleName=role_name_2,
            AssumeRolePolicyDocument=str_assume_role_policy_doc,
            Description="string",
        )

        roles = aws_client.iam.list_roles(PathPrefix="/my")
        assert len(roles["Roles"]) == 1
        assert roles["Roles"][0]["Path"] == "/myPath/"
        assert roles["Roles"][0]["RoleName"] == role_name_2