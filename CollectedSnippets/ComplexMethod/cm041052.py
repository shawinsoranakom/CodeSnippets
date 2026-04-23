def create(
        self,
        request: ResourceRequest[CloudFormationStackProperties],
    ) -> ProgressEvent[CloudFormationStackProperties]:
        """
        Create a new resource.

        Primary identifier fields:
          - /properties/Id

        Required properties:
          - TemplateURL



        Read-only properties:
          - /properties/Id



        """
        model = request.desired_state

        # TODO: validations

        if not request.custom_context.get(REPEATED_INVOCATION):
            if not model.get("StackName"):
                model["StackName"] = util.generate_default_name(
                    request.stack_name, request.logical_resource_id
                )

            create_params = util.select_attributes(
                model,
                [
                    "StackName",
                    "Parameters",
                    "NotificationARNs",
                    "TemplateURL",
                    "TimeoutInMinutes",
                    "Tags",
                ],
            )

            create_params["Capabilities"] = [
                "CAPABILITY_IAM",
                "CAPABILITY_NAMED_IAM",
                "CAPABILITY_AUTO_EXPAND",
            ]

            create_params["Parameters"] = [
                {
                    "ParameterKey": k,
                    "ParameterValue": str(v).lower() if isinstance(v, bool) else str(v),
                }
                for k, v in create_params.get("Parameters", {}).items()
            ]

            result = request.aws_client_factory.cloudformation.create_stack(**create_params)
            model["Id"] = result["StackId"]

            request.custom_context[REPEATED_INVOCATION] = True
            return ProgressEvent(
                status=OperationStatus.IN_PROGRESS,
                resource_model=model,
                custom_context=request.custom_context,
            )

        stack = request.aws_client_factory.cloudformation.describe_stacks(StackName=model["Id"])[
            "Stacks"
        ][0]
        match stack["StackStatus"]:
            case "CREATE_COMPLETE":
                # only store nested stack outputs when we know the deploy has completed
                model["Outputs"] = {
                    o["OutputKey"]: o["OutputValue"] for o in stack.get("Outputs", [])
                }
                return ProgressEvent(
                    status=OperationStatus.SUCCESS,
                    resource_model=model,
                    custom_context=request.custom_context,
                )
            case "CREATE_IN_PROGRESS":
                return ProgressEvent(
                    status=OperationStatus.IN_PROGRESS,
                    resource_model=model,
                    custom_context=request.custom_context,
                )
            case "CREATE_FAILED":
                return ProgressEvent(
                    status=OperationStatus.FAILED,
                    resource_model=model,
                    custom_context=request.custom_context,
                )
            case _:
                raise Exception(f"Unexpected status: {stack['StackStatus']}")