def create_stack_instances(
        self,
        context: RequestContext,
        request: CreateStackInstancesInput,
    ) -> CreateStackInstancesOutput:
        state = get_cloudformation_store(context.account_id, context.region)

        set_name = request.get("StackSetName")
        stack_set = [sset for sset in state.stack_sets.values() if sset.stack_set_name == set_name]

        if not stack_set:
            return not_found_error(f'Stack set named "{set_name}" does not exist')

        stack_set = stack_set[0]
        op_id = request.get("OperationId") or short_uid()
        sset_meta = stack_set.metadata
        accounts = request["Accounts"]
        regions = request["Regions"]

        stacks_to_await = []
        for account in accounts:
            for region in regions:
                # deploy new stack
                LOG.debug(
                    'Deploying instance for stack set "%s" in account: %s region %s',
                    set_name,
                    account,
                    region,
                )
                cf_client = connect_to(aws_access_key_id=account, region_name=region).cloudformation
                kwargs = select_attributes(sset_meta, ["TemplateBody"]) or select_attributes(
                    sset_meta, ["TemplateURL"]
                )
                stack_name = f"sset-{set_name}-{account}"

                # skip creation of existing stacks
                if find_stack(context.account_id, context.region, stack_name):
                    continue

                result = cf_client.create_stack(StackName=stack_name, **kwargs)
                stacks_to_await.append((stack_name, account, region))
                # store stack instance
                instance = {
                    "StackSetId": sset_meta["StackSetId"],
                    "OperationId": op_id,
                    "Account": account,
                    "Region": region,
                    "StackId": result["StackId"],
                    "Status": "CURRENT",
                    "StackInstanceStatus": {"DetailedStatus": "SUCCEEDED"},
                }
                instance = StackInstance(instance)
                stack_set.stack_instances.append(instance)

        # wait for completion of stack
        for stack_name, account_id, region_name in stacks_to_await:
            client = connect_to(
                aws_access_key_id=account_id, region_name=region_name
            ).cloudformation
            client.get_waiter("stack_create_complete").wait(StackName=stack_name)

        # record operation
        operation = {
            "OperationId": op_id,
            "StackSetId": stack_set.metadata["StackSetId"],
            "Action": "CREATE",
            "Status": "SUCCEEDED",
        }
        stack_set.operations[op_id] = operation

        return CreateStackInstancesOutput(OperationId=op_id)