def inner(
        snapshot,
        t1: dict | str,
        t2: dict | str,
        p1: dict | None = None,
        p2: dict | None = None,
        custom_update_step: Callable[[], None] | None = None,
    ) -> str:
        """
        :return: stack id
        """
        snapshot.add_transformer(snapshot.transform.cloudformation_api())

        if isinstance(t1, dict):
            t1 = json.dumps(t1)
        elif isinstance(t1, str):
            with open(t1) as infile:
                t1 = infile.read()
        if isinstance(t2, dict):
            t2 = json.dumps(t2)
        elif isinstance(t2, str):
            with open(t2) as infile:
                t2 = infile.read()

        p1 = p1 or {}
        p2 = p2 or {}

        # deploy original stack
        change_set_details = aws_client_no_retry.cloudformation.create_change_set(
            StackName=stack_name,
            ChangeSetName=change_set_name,
            TemplateBody=t1,
            ChangeSetType="CREATE",
            Capabilities=[
                "CAPABILITY_IAM",
                "CAPABILITY_NAMED_IAM",
                "CAPABILITY_AUTO_EXPAND",
            ],
            Parameters=[{"ParameterKey": k, "ParameterValue": v} for (k, v) in p1.items()],
        )
        snapshot.match("create-change-set-1", change_set_details)
        stack_id = change_set_details["StackId"]
        change_set_id = change_set_details["Id"]
        aws_client_no_retry.cloudformation.get_waiter("change_set_create_complete").wait(
            ChangeSetName=change_set_id
        )
        cleanups.append(
            lambda: call_safe(
                aws_client_no_retry.cloudformation.delete_change_set,
                kwargs={"ChangeSetName": change_set_id},
            )
        )

        describe_change_set_with_prop_values = (
            aws_client_no_retry.cloudformation.describe_change_set(
                ChangeSetName=change_set_id, IncludePropertyValues=True
            )
        )
        _normalise_describe_change_set_output(describe_change_set_with_prop_values)
        snapshot.match("describe-change-set-1-prop-values", describe_change_set_with_prop_values)

        describe_change_set_without_prop_values = (
            aws_client_no_retry.cloudformation.describe_change_set(
                ChangeSetName=change_set_id, IncludePropertyValues=False
            )
        )
        _normalise_describe_change_set_output(describe_change_set_without_prop_values)
        snapshot.match("describe-change-set-1", describe_change_set_without_prop_values)

        execute_results = aws_client_no_retry.cloudformation.execute_change_set(
            ChangeSetName=change_set_id
        )
        snapshot.match("execute-change-set-1", execute_results)
        aws_client_no_retry.cloudformation.get_waiter("stack_create_complete").wait(
            StackName=stack_id
        )

        # ensure stack deletion
        cleanups.append(
            lambda: call_safe(
                aws_client_no_retry.cloudformation.delete_stack, kwargs={"StackName": stack_id}
            )
        )

        describe = aws_client_no_retry.cloudformation.describe_stacks(StackName=stack_id)["Stacks"][
            0
        ]
        snapshot.match("post-create-1-describe", describe)

        # run any custom steps if present
        if custom_update_step:
            custom_update_step()

        # update stack
        change_set_details = aws_client_no_retry.cloudformation.create_change_set(
            StackName=stack_name,
            ChangeSetName=change_set_name,
            TemplateBody=t2,
            ChangeSetType="UPDATE",
            Parameters=[{"ParameterKey": k, "ParameterValue": v} for (k, v) in p2.items()],
            Capabilities=[
                "CAPABILITY_IAM",
                "CAPABILITY_NAMED_IAM",
                "CAPABILITY_AUTO_EXPAND",
            ],
        )
        snapshot.match("create-change-set-2", change_set_details)
        stack_id = change_set_details["StackId"]
        change_set_id = change_set_details["Id"]
        try:
            aws_client_no_retry.cloudformation.get_waiter("change_set_create_complete").wait(
                ChangeSetName=change_set_id
            )
        except WaiterError as e:
            desc = aws_client_no_retry.cloudformation.describe_change_set(
                ChangeSetName=change_set_id
            )
            raise RuntimeError(f"Change set deployment failed: {desc}") from e

        describe_change_set_with_prop_values = (
            aws_client_no_retry.cloudformation.describe_change_set(
                ChangeSetName=change_set_id, IncludePropertyValues=True
            )
        )
        _normalise_describe_change_set_output(describe_change_set_with_prop_values)
        snapshot.match("describe-change-set-2-prop-values", describe_change_set_with_prop_values)

        describe_change_set_without_prop_values = (
            aws_client_no_retry.cloudformation.describe_change_set(
                ChangeSetName=change_set_id, IncludePropertyValues=False
            )
        )
        _normalise_describe_change_set_output(describe_change_set_without_prop_values)
        snapshot.match("describe-change-set-2", describe_change_set_without_prop_values)

        execute_results = aws_client_no_retry.cloudformation.execute_change_set(
            ChangeSetName=change_set_id
        )
        snapshot.match("execute-change-set-2", execute_results)
        aws_client_no_retry.cloudformation.get_waiter("stack_update_complete").wait(
            StackName=stack_id
        )

        describe = aws_client_no_retry.cloudformation.describe_stacks(StackName=stack_id)["Stacks"][
            0
        ]
        snapshot.match("post-create-2-describe", describe)

        # delete stack
        aws_client_no_retry.cloudformation.delete_stack(StackName=stack_id)
        aws_client_no_retry.cloudformation.get_waiter("stack_delete_complete").wait(
            StackName=stack_id
        )
        describe = aws_client_no_retry.cloudformation.describe_stacks(StackName=stack_id)["Stacks"][
            0
        ]
        snapshot.match("delete-describe", describe)

        events = capture_per_resource_events(stack_id)
        snapshot.match("per-resource-events", events)

        return stack_id