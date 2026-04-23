def get_template(
        self,
        context: RequestContext,
        stack_name: StackName = None,
        change_set_name: ChangeSetNameOrId = None,
        template_stage: TemplateStage = None,
        **kwargs,
    ) -> GetTemplateOutput:
        if change_set_name:
            stack = find_change_set(
                context.account_id, context.region, stack_name=stack_name, cs_name=change_set_name
            )
        else:
            stack = find_stack(context.account_id, context.region, stack_name)
        if not stack:
            return stack_not_found_error(stack_name)

        if template_stage == TemplateStage.Processed and "Transform" in stack.template_body:
            copy_template = clone(stack.template_original)
            for key in [
                "ChangeSetName",
                "StackName",
                "StackId",
                "Transform",
                "Conditions",
                "Mappings",
            ]:
                copy_template.pop(key, None)
            for key in ["Parameters", "Outputs"]:
                if key in copy_template and not copy_template[key]:
                    copy_template.pop(key)
            for resource in copy_template.get("Resources", {}).values():
                resource.pop("LogicalResourceId", None)
            template_body = json.dumps(copy_template)
        else:
            template_body = stack.template_body

        return GetTemplateOutput(
            TemplateBody=template_body,
            StagesAvailable=[TemplateStage.Original, TemplateStage.Processed],
        )