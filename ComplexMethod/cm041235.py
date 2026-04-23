def _deploy(
        *,
        is_update: bool | None = False,
        stack_name: str | None = None,
        change_set_name: str | None = None,
        template: str | None = None,
        template_path: str | os.PathLike | None = None,
        template_mapping: dict[str, Any] | None = None,
        parameters: dict[str, str] | None = None,
        role_arn: str | None = None,
        max_wait: int | None = None,
        delay_between_polls: int | None = 2,
        custom_aws_client: ServiceLevelClientFactory | None = None,
        raw_parameters: list[Parameter] | None = None,
    ) -> DeployResult:
        if is_update:
            assert stack_name
        stack_name = stack_name or f"stack-{short_uid()}"
        change_set_name = change_set_name or f"change-set-{short_uid()}"

        if max_wait is None:
            max_wait = 1800 if is_aws_cloud() else 180

        if template_path is not None:
            template = load_template_file(template_path)
            if template is None:
                raise RuntimeError(f"Could not find file {os.path.realpath(template_path)}")
        template_rendered = render_template(template, **(template_mapping or {}))

        kwargs = CreateChangeSetInput(
            StackName=stack_name,
            ChangeSetName=change_set_name,
            TemplateBody=template_rendered,
            Capabilities=["CAPABILITY_AUTO_EXPAND", "CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"],
            ChangeSetType=("UPDATE" if is_update else "CREATE"),
        )
        kwargs["Parameters"] = []
        if parameters:
            kwargs["Parameters"] = [
                Parameter(ParameterKey=k, ParameterValue=v) for (k, v) in parameters.items()
            ]
        elif raw_parameters:
            kwargs["Parameters"] = raw_parameters

        if role_arn is not None:
            kwargs["RoleARN"] = role_arn

        cfn_aws_client = custom_aws_client if custom_aws_client is not None else aws_client

        response = cfn_aws_client.cloudformation.create_change_set(**kwargs)

        change_set_id = response["Id"]
        stack_id = response["StackId"]

        try:
            cfn_aws_client.cloudformation.get_waiter(WAITER_CHANGE_SET_CREATE_COMPLETE).wait(
                ChangeSetName=change_set_id
            )
        except botocore.exceptions.WaiterError as e:
            change_set = cfn_aws_client.cloudformation.describe_change_set(
                ChangeSetName=change_set_id
            )
            raise Exception(f"{change_set['Status']}: {change_set.get('StatusReason')}") from e

        cfn_aws_client.cloudformation.execute_change_set(ChangeSetName=change_set_id)
        stack_waiter = cfn_aws_client.cloudformation.get_waiter(
            WAITER_STACK_UPDATE_COMPLETE if is_update else WAITER_STACK_CREATE_COMPLETE
        )

        try:
            stack_waiter.wait(
                StackName=stack_id,
                WaiterConfig={
                    "Delay": delay_between_polls,
                    "MaxAttempts": max_wait / delay_between_polls,
                },
            )
        except botocore.exceptions.WaiterError as e:
            raise StackDeployError(
                cfn_aws_client.cloudformation.describe_stacks(StackName=stack_id)["Stacks"][0],
                cfn_aws_client.cloudformation.describe_stack_events(StackName=stack_id)[
                    "StackEvents"
                ],
            ) from e

        describe_stack_res = cfn_aws_client.cloudformation.describe_stacks(StackName=stack_id)[
            "Stacks"
        ][0]
        outputs = describe_stack_res.get("Outputs", [])

        mapped_outputs = {o["OutputKey"]: o.get("OutputValue") for o in outputs}

        def _destroy_stack():
            cfn_aws_client.cloudformation.delete_stack(StackName=stack_id)
            cfn_aws_client.cloudformation.get_waiter(WAITER_STACK_DELETE_COMPLETE).wait(
                StackName=stack_id,
                WaiterConfig={
                    "Delay": delay_between_polls,
                    "MaxAttempts": max_wait / delay_between_polls,
                },
            )

        state.append((stack_id, _destroy_stack))

        return DeployResult(
            change_set_id, stack_id, stack_name, change_set_name, mapped_outputs, _destroy_stack
        )