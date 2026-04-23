def delete_stack_instances(
        self,
        context: RequestContext,
        request: DeleteStackInstancesInput,
    ) -> DeleteStackInstancesOutput:
        op_id = request.get("OperationId") or short_uid()

        accounts = request["Accounts"]
        regions = request["Regions"]

        state = get_cloudformation_store(context.account_id, context.region)
        stack_sets = state.stack_sets.values()

        set_name = request.get("StackSetName")
        stack_set = next((sset for sset in stack_sets if sset.stack_set_name == set_name), None)

        if not stack_set:
            return not_found_error(f'Stack set named "{set_name}" does not exist')

        for account in accounts:
            for region in regions:
                instance = find_stack_instance(stack_set, account, region)
                if instance:
                    stack_set.stack_instances.remove(instance)

        # record operation
        operation = {
            "OperationId": op_id,
            "StackSetId": stack_set.metadata["StackSetId"],
            "Action": "DELETE",
            "Status": "SUCCEEDED",
        }
        stack_set.operations[op_id] = operation

        return DeleteStackInstancesOutput(OperationId=op_id)