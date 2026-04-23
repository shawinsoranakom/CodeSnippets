def update_usage_plan(
        self,
        context: RequestContext,
        usage_plan_id: String,
        patch_operations: ListOfPatchOperation = None,
        **kwargs,
    ) -> UsagePlan:
        for patch_op in patch_operations:
            if patch_op.get("op") == "remove" and patch_op.get("path") == "/apiStages":
                if not (api_stage_id := patch_op.get("value")):
                    raise BadRequestException("Invalid API Stage specified")
                if not len(split_stage_id := api_stage_id.split(":")) == 2:
                    raise BadRequestException("Invalid API Stage specified")
                rest_api_id, stage_name = split_stage_id
                moto_backend = apigw_models.apigateway_backends[context.account_id][context.region]
                if not (rest_api := moto_backend.apis.get(rest_api_id)):
                    raise NotFoundException(
                        f"Invalid API Stage {{api: {rest_api_id}, stage: {stage_name}}} specified for usageplan {usage_plan_id}"
                    )
                if stage_name not in rest_api.stages:
                    raise NotFoundException(
                        f"Invalid API Stage {{api: {rest_api_id}, stage: {stage_name}}} specified for usageplan {usage_plan_id}"
                    )

        usage_plan = call_moto(context=context)
        if not usage_plan.get("quota"):
            usage_plan.pop("quota", None)

        usage_plan_arn = f"arn:{get_partition(context.region)}:apigateway:{context.region}::/usageplans/{usage_plan_id}"
        existing_tags = get_apigateway_store(context=context).TAGS.get(usage_plan_arn, {})
        if "tags" not in usage_plan:
            usage_plan["tags"] = existing_tags
        else:
            usage_plan["tags"].update(existing_tags)

        fix_throttle_and_quota_from_usage_plan(usage_plan)

        return usage_plan