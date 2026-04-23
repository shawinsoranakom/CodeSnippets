def update(
        self,
        request: ResourceRequest[ApiGatewayUsagePlanProperties],
    ) -> ProgressEvent[ApiGatewayUsagePlanProperties]:
        """
        Update a resource

        IAM permissions required:
          - apigateway:GET
          - apigateway:DELETE
          - apigateway:PATCH
          - apigateway:PUT
        """
        model = request.desired_state
        apigw = request.aws_client_factory.apigateway

        parameters_to_select = [
            "UsagePlanName",
            "Description",
            "ApiStages",
            "Quota",
            "Throttle",
            "Tags",
        ]
        update_config_props = util.select_attributes(model, parameters_to_select)

        updated_tags = update_config_props.pop("Tags", [])

        usage_plan_id = request.previous_state["Id"]

        patch_operations = []

        for parameter in update_config_props:
            value = update_config_props[parameter]
            if parameter == "ApiStages":
                for stage in value:
                    patch_operations.append(
                        {
                            "op": "replace",
                            "path": f"/{first_char_to_lower(parameter)}",
                            "value": f"{stage['ApiId']}:{stage['Stage']}",
                        }
                    )

                    if "Throttle" in stage:
                        patch_operations.append(
                            {
                                "op": "replace",
                                "path": f"/{first_char_to_lower(parameter)}/{stage['ApiId']}:{stage['Stage']}",
                                "value": json.dumps(stage["Throttle"]),
                            }
                        )

            elif isinstance(value, dict):
                for item in value:
                    last_value = value[item]
                    path = f"/{first_char_to_lower(parameter)}/{first_char_to_lower(item)}"
                    patch_operations.append({"op": "replace", "path": path, "value": last_value})
            else:
                patch_operations.append(
                    {"op": "replace", "path": f"/{first_char_to_lower(parameter)}", "value": value}
                )
        apigw.update_usage_plan(usagePlanId=usage_plan_id, patchOperations=patch_operations)

        if updated_tags:
            tags = {tag["Key"]: tag["Value"] for tag in updated_tags}
            usage_plan_arn = f"arn:{get_partition(request.region_name)}:apigateway:{request.region_name}::/usageplans/{usage_plan_id}"
            apigw.tag_resource(resourceArn=usage_plan_arn, tags=tags)

        return ProgressEvent(
            status=OperationStatus.SUCCESS,
            resource_model={**request.previous_state, **request.desired_state},
            custom_context=request.custom_context,
        )