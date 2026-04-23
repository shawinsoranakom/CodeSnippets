def create_stack_instances(
        self,
        context: RequestContext,
        request: CreateStackInstancesInput,
    ) -> CreateStackInstancesOutput:
        state = get_cloudformation_store(context.account_id, context.region)

        stack_set_name = request["StackSetName"]
        stack_set = find_stack_set_v2(state, stack_set_name)
        if not stack_set:
            raise StackSetNotFoundError(stack_set_name)

        op_id = request.get("OperationId") or short_uid()
        accounts = request["Accounts"]
        regions = request["Regions"]

        stacks_to_await = []
        for account in accounts:
            for region in regions:
                # deploy new stack
                LOG.debug(
                    'Deploying instance for stack set "%s" in account: %s region %s',
                    stack_set_name,
                    account,
                    region,
                )
                cf_client = connect_to(aws_access_key_id=account, region_name=region).cloudformation
                if stack_set.template_body:
                    kwargs = {
                        "TemplateBody": stack_set.template_body,
                    }
                elif stack_set.template_url:
                    kwargs = {
                        "TemplateURL": stack_set.template_url,
                    }
                else:
                    # TODO: wording
                    raise ValueError("Neither StackSet Template URL nor TemplateBody provided")
                stack_name = f"sset-{stack_set_name}-{account}-{region}"

                # skip creation of existing stacks
                if find_stack_v2(state, stack_name):
                    continue

                result = cf_client.create_stack(StackName=stack_name, **kwargs)
                # store stack instance
                stack_instance = StackInstance(
                    account_id=account,
                    region_name=region,
                    stack_set_id=stack_set.stack_set_id,
                    operation_id=op_id,
                    stack_id=result["StackId"],
                )
                stack_set.stack_instances.append(stack_instance)

                stacks_to_await.append((stack_name, account, region))

        # wait for completion of stack
        for stack_name, account_id, region_name in stacks_to_await:
            client = connect_to(
                aws_access_key_id=account_id, region_name=region_name
            ).cloudformation
            client.get_waiter("stack_create_complete").wait(StackName=stack_name)

        # record operation
        operation = StackSetOperation(
            OperationId=op_id,
            StackSetId=stack_set.stack_set_id,
            Action=StackSetOperationAction.CREATE,
            Status=StackSetOperationStatus.SUCCEEDED,
        )
        stack_set.operations[op_id] = operation

        return CreateStackInstancesOutput(OperationId=op_id)