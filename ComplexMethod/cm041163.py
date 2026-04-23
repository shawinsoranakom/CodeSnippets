def validate_api_key(self, api_key_value, context: RestApiInvocationContext) -> ApiKey | None:
        api_id = context.api_id
        stage = context.stage
        account_id = context.account_id
        region = context.region

        # Get usage plans from the store
        usage_plans = get_usage_plans(account_id=account_id, region_name=region)

        # Loop through usage plans and keep ids of the plans associated with the deployment stage
        usage_plan_ids = []
        for usage_plan in usage_plans:
            api_stages = usage_plan.get("apiStages", [])
            usage_plan_ids.extend(
                usage_plan.get("id")
                for api_stage in api_stages
                if (api_stage.get("stage") == stage and api_stage.get("apiId") == api_id)
            )
        if not usage_plan_ids:
            LOG.debug("No associated usage plans found stage '%s'", stage)
            return

        # Loop through plans with an association with the stage find a key with matching value
        for usage_plan_id in usage_plan_ids:
            usage_plan_keys = get_usage_plan_keys(
                usage_plan_id=usage_plan_id, account_id=account_id, region_name=region
            )
            for key in usage_plan_keys:
                if key["value"] == api_key_value:
                    api_key = get_api_key(
                        api_key_id=key["id"], account_id=account_id, region_name=region
                    )
                    LOG.debug("Found Api Key '%s'", api_key["id"])
                    return api_key if api_key["enabled"] else None