def find_stack_v2(state: CloudFormationStore, stack_name: str | None) -> Stack | None:
    if stack_name:
        if is_stack_arn(stack_name):
            return state.stacks_v2[stack_name]
        else:
            stack_candidates = []
            for stack in state.stacks_v2.values():
                if stack.stack_name == stack_name and stack.status != StackStatus.DELETE_COMPLETE:
                    stack_candidates.append(stack)
            if len(stack_candidates) == 0:
                return None
            elif len(stack_candidates) > 1:
                raise RuntimeError("Programing error, duplicate stacks found")
            else:
                return stack_candidates[0]
    else:
        raise ValueError("No stack name specified when finding stack")