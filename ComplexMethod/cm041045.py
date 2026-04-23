def get_template_summary(
        self,
        context: RequestContext,
        request: GetTemplateSummaryInput,
    ) -> GetTemplateSummaryOutput:
        state = get_cloudformation_store(context.account_id, context.region)
        stack_name = request.get("StackName")

        if stack_name:
            stack = find_stack_v2(state, stack_name)
            if not stack:
                raise StackNotFoundError(stack_name)

            if stack.status == StackStatus.REVIEW_IN_PROGRESS:
                raise ValidationError(
                    "GetTemplateSummary cannot be called on REVIEW_IN_PROGRESS stacks."
                )

            template = stack.template
        else:
            template_body = request.get("TemplateBody")
            # s3 or secretsmanager url
            template_url = request.get("TemplateURL")

            # validate and resolve template
            if template_body and template_url:
                raise ValidationError(
                    "Specify exactly one of 'TemplateBody' or 'TemplateUrl'"
                )  # TODO: check proper message

            if not template_body and not template_url:
                raise ValidationError(
                    "Specify exactly one of 'TemplateBody' or 'TemplateUrl'"
                )  # TODO: check proper message

            template_body = api_utils.extract_template_body(request)
            template = template_preparer.parse_template(template_body)

        id_summaries = defaultdict(list)
        if "Resources" not in template:
            raise ValidationError(
                "Template format error: At least one Resources member must be defined."
            )

        for resource_id, resource in template["Resources"].items():
            res_type = resource["Type"]
            id_summaries[res_type].append(resource_id)

        summarized_parameters = []
        for parameter_id, parameter_body in template.get("Parameters", {}).items():
            summarized_parameters.append(
                {
                    "ParameterKey": parameter_id,
                    "DefaultValue": parameter_body.get("Default"),
                    "ParameterType": parameter_body["Type"],
                    "Description": parameter_body.get("Description"),
                }
            )
        result = GetTemplateSummaryOutput(
            Parameters=summarized_parameters,
            Metadata=template.get("Metadata"),
            ResourceIdentifierSummaries=[
                {"ResourceType": key, "LogicalResourceIds": values}
                for key, values in id_summaries.items()
            ],
            ResourceTypes=list(id_summaries.keys()),
            Version=template.get("AWSTemplateFormatVersion", "2010-09-09"),
        )

        return result