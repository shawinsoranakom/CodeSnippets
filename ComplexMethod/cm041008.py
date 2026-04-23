def create(
        self,
        request: ResourceRequest[IAMRoleProperties],
    ) -> ProgressEvent[IAMRoleProperties]:
        """
        Create a new resource.

        Primary identifier fields:
          - /properties/RoleName

        Required properties:
          - AssumeRolePolicyDocument

        Create-only properties:
          - /properties/Path
          - /properties/RoleName

        Read-only properties:
          - /properties/Arn
          - /properties/RoleId

        IAM permissions required:
          - iam:CreateRole
          - iam:PutRolePolicy
          - iam:AttachRolePolicy
          - iam:GetRolePolicy <- not in use right now

        """
        model = request.desired_state
        iam = request.aws_client_factory.iam

        # defaults
        role_name = model.get("RoleName")
        if not role_name:
            role_name = util.generate_default_name(request.stack_name, request.logical_resource_id)
            model["RoleName"] = role_name

        create_role_response = iam.create_role(
            **{
                k: v
                for k, v in model.items()
                if k not in ["ManagedPolicyArns", "Policies", "AssumeRolePolicyDocument"]
            },
            AssumeRolePolicyDocument=json.dumps(model["AssumeRolePolicyDocument"]),
        )

        # attach managed policies
        policy_arns = model.get("ManagedPolicyArns", [])
        for arn in policy_arns:
            iam.attach_role_policy(RoleName=role_name, PolicyArn=arn)

        # add inline policies
        inline_policies = model.get("Policies", [])
        for policy in inline_policies:
            if not isinstance(policy, dict):
                request.logger.info(
                    'Invalid format of policy for IAM role "%s": %s',
                    model.get("RoleName"),
                    policy,
                )
                continue
            pol_name = policy.get("PolicyName")

            # get policy document - make sure we're resolving references in the policy doc
            doc = dict(policy["PolicyDocument"])
            doc = util.remove_none_values(doc)

            doc["Version"] = doc.get("Version") or IAM_POLICY_VERSION
            statements = doc["Statement"]
            statements = statements if isinstance(statements, list) else [statements]
            for statement in statements:
                if isinstance(statement.get("Resource"), list):
                    # filter out empty resource strings
                    statement["Resource"] = [r for r in statement["Resource"] if r]
            doc = json.dumps(doc)
            iam.put_role_policy(
                RoleName=model["RoleName"],
                PolicyName=pol_name,
                PolicyDocument=doc,
            )
        model["Arn"] = create_role_response["Role"]["Arn"]
        model["RoleId"] = create_role_response["Role"]["RoleId"]

        return ProgressEvent(status=OperationStatus.SUCCESS, resource_model=model)