def get_policies_from_principal(backend: IAMBackend, principal_arn: str) -> list[dict]:
        policies = []
        if ":role" in principal_arn:
            role_name = principal_arn.split("/")[-1]

            policies.append(backend.get_role(role_name=role_name).assume_role_policy_document)

            policy_names = backend.list_role_policies(role_name=role_name)
            policies.extend(
                [
                    backend.get_role_policy(role_name=role_name, policy_name=policy_name)[1]
                    for policy_name in policy_names
                ]
            )

            attached_policies, _ = backend.list_attached_role_policies(role_name=role_name)
            policies.extend([policy.document for policy in attached_policies])

        if ":group" in principal_arn:
            group_name = principal_arn.split("/")[-1]
            policy_names = backend.list_group_policies(group_name=group_name)
            policies.extend(
                [
                    backend.get_group_policy(group_name=group_name, policy_name=policy_name)[1]
                    for policy_name in policy_names
                ]
            )

            attached_policies, _ = backend.list_attached_group_policies(group_name=group_name)
            policies.extend([policy.document for policy in attached_policies])

        if ":user" in principal_arn:
            user_name = principal_arn.split("/")[-1]
            policy_names = backend.list_user_policies(user_name=user_name)
            policies.extend(
                [
                    backend.get_user_policy(user_name=user_name, policy_name=policy_name)[1]
                    for policy_name in policy_names
                ]
            )

            attached_policies, _ = backend.list_attached_user_policies(user_name=user_name)
            policies.extend([policy.document for policy in attached_policies])

        return policies