def create_rest_apigw(aws_client_factory):
    rest_apis = []
    retry_boto_config = None
    if is_aws_cloud():
        retry_boto_config = botocore.config.Config(
            # Api gateway can throttle requests pretty heavily. Leading to potentially undeleted apis
            retries={"max_attempts": 10, "mode": "adaptive"}
        )

    def _create_apigateway_function(**kwargs):
        client_region_name = kwargs.pop("region_name", None)
        apigateway_client = aws_client_factory(
            region_name=client_region_name, config=retry_boto_config
        ).apigateway
        kwargs.setdefault("name", f"api-{short_uid()}")

        response = apigateway_client.create_rest_api(**kwargs)
        api_id = response.get("id")
        rest_apis.append((api_id, client_region_name))

        return api_id, response.get("name"), response.get("rootResourceId")

    yield _create_apigateway_function

    for rest_api_id, _client_region_name in rest_apis:
        apigateway_client = aws_client_factory(
            region_name=_client_region_name,
            config=retry_boto_config,
        ).apigateway
        # First, retrieve the usage plans associated with the REST API
        usage_plan_ids = []
        usage_plans = apigateway_client.get_usage_plans()
        for item in usage_plans.get("items", []):
            api_stages = item.get("apiStages", [])
            usage_plan_ids.extend(
                item.get("id") for api_stage in api_stages if api_stage.get("apiId") == rest_api_id
            )

        # Then delete the API, as you can't delete the UsagePlan if a stage is associated with it
        with contextlib.suppress(Exception):
            apigateway_client.delete_rest_api(restApiId=rest_api_id)

        # finally delete the usage plans and the API Keys linked to it
        for usage_plan_id in usage_plan_ids:
            usage_plan_keys = apigateway_client.get_usage_plan_keys(usagePlanId=usage_plan_id)
            for key in usage_plan_keys.get("items", []):
                apigateway_client.delete_api_key(apiKey=key["id"])
            apigateway_client.delete_usage_plan(usagePlanId=usage_plan_id)