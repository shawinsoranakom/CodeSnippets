def describe_stacks(
        self,
        context: RequestContext,
        stack_name: StackName = None,
        next_token: NextToken = None,
        **kwargs,
    ) -> DescribeStacksOutput:
        # TODO: test & implement pagination
        state = get_cloudformation_store(context.account_id, context.region)

        if stack_name:
            if ARN_STACK_REGEX.match(stack_name):
                # we can get the stack directly since we index the store by ARN/stackID
                stack = state.stacks.get(stack_name)
                stacks = [stack.describe_details()] if stack else []
            else:
                # otherwise we have to find the active stack with the given name
                stack_candidates: list[Stack] = [
                    s for stack_arn, s in state.stacks.items() if s.stack_name == stack_name
                ]
                active_stack_candidates = [
                    s for s in stack_candidates if self._stack_status_is_active(s.status)
                ]
                stacks = [s.describe_details() for s in active_stack_candidates]
        else:
            # return all active stacks
            stack_list = list(state.stacks.values())
            stacks = [
                s.describe_details() for s in stack_list if self._stack_status_is_active(s.status)
            ]

        if stack_name and not stacks:
            raise ValidationError(f"Stack with id {stack_name} does not exist")

        return DescribeStacksOutput(Stacks=stacks)