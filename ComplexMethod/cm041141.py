def validate_api_key(api_key: str, invocation_context: ApiInvocationContext):
    usage_plan_ids = []
    client = connect_to(
        aws_access_key_id=invocation_context.account_id, region_name=invocation_context.region_name
    ).apigateway

    usage_plans = client.get_usage_plans()
    for item in usage_plans.get("items", []):
        api_stages = item.get("apiStages", [])
        usage_plan_ids.extend(
            item.get("id")
            for api_stage in api_stages
            if (
                api_stage.get("stage") == invocation_context.stage
                and api_stage.get("apiId") == invocation_context.api_id
            )
        )
    for usage_plan_id in usage_plan_ids:
        usage_plan_keys = client.get_usage_plan_keys(usagePlanId=usage_plan_id)
        for key in usage_plan_keys.get("items", []):
            if key.get("value") == api_key:
                # check if the key is enabled
                api_key = client.get_api_key(apiKey=key.get("id"))
                return api_key.get("enabled") in ("true", True)

    return False