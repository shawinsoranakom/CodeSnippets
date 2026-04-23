def create_service_linked_role(
        self,
        context: RequestContext,
        aws_service_name: groupNameType,
        description: roleDescriptionType = None,
        custom_suffix: customSuffixType = None,
        **kwargs,
    ) -> CreateServiceLinkedRoleResponse:
        policy_doc = json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": aws_service_name},
                        "Action": "sts:AssumeRole",
                    }
                ],
            }
        )
        service_role_data = SERVICE_LINKED_ROLES.get(aws_service_name)

        path = f"{SERVICE_LINKED_ROLE_PATH_PREFIX}/{aws_service_name}/"
        if service_role_data:
            if custom_suffix and not service_role_data["suffix_allowed"]:
                raise InvalidInputException(f"Custom suffix is not allowed for {aws_service_name}")
            role_name = service_role_data.get("role_name")
            attached_policies = service_role_data["attached_policies"]
        else:
            role_name = f"AWSServiceRoleFor{aws_service_name.split('.')[0].capitalize()}"
            attached_policies = []
        if custom_suffix:
            role_name = f"{role_name}_{custom_suffix}"
        backend = get_iam_backend(context)

        # check for role duplicates
        for role in backend.roles.values():
            if role.name == role_name:
                raise InvalidInputException(
                    f"Service role name {role_name} has been taken in this account, please try a different suffix."
                )

        role = backend.create_role(
            role_name=role_name,
            assume_role_policy_document=policy_doc,
            path=path,
            permissions_boundary="",
            description=description,
            tags={},
            max_session_duration=3600,
            linked_service=aws_service_name,
        )
        # attach policies
        for policy in attached_policies:
            try:
                backend.attach_role_policy(policy, role_name)
            except Exception as e:
                LOG.warning(
                    "Policy %s for service linked role %s does not exist: %s",
                    policy,
                    aws_service_name,
                    e,
                )

        res_role = self.moto_role_to_role_type(role)
        return CreateServiceLinkedRoleResponse(Role=res_role)