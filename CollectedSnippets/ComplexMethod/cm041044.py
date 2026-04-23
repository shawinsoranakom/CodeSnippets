def get_template(
        self,
        context: RequestContext,
        stack_name: StackName = None,
        change_set_name: ChangeSetNameOrId = None,
        template_stage: TemplateStage = None,
        **kwargs,
    ) -> GetTemplateOutput:
        state = get_cloudformation_store(context.account_id, context.region)
        if change_set_name:
            if not is_changeset_arn(change_set_name) and not stack_name:
                raise ValidationError("StackName is a required parameter.")

            change_set = find_change_set_v2(state, change_set_name, stack_name=stack_name)
            if not change_set:
                raise ChangeSetNotFoundException(f"ChangeSet [{change_set_name}] does not exist")
            stack = change_set.stack
        elif stack_name:
            stack = find_stack_v2(state, stack_name)
            if not stack:
                raise StackNotFoundError(
                    stack_name, message_override=f"Stack with id {stack_name} does not exist"
                )
        else:
            raise ValidationError("StackName is required if ChangeSetName is not specified.")

        if template_stage == TemplateStage.Processed and "Transform" in stack.template_body:
            template_body = json.dumps(stack.processed_template)
        else:
            template_body = stack.template_body

        return GetTemplateOutput(
            TemplateBody=template_body,
            StagesAvailable=[TemplateStage.Original, TemplateStage.Processed],
        )