def create(
        self,
        request: ResourceRequest[LambdaVersionProperties],
    ) -> ProgressEvent[LambdaVersionProperties]:
        """
        Create a new resource.

        Primary identifier fields:
          - /properties/Id

        Required properties:
          - FunctionName

        Create-only properties:
          - /properties/FunctionName

        Read-only properties:
          - /properties/Id
          - /properties/Version



        """
        model = request.desired_state
        lambda_client = request.aws_client_factory.lambda_
        ctx = request.custom_context

        params = util.select_attributes(model, ["FunctionName", "CodeSha256", "Description"])

        if not ctx.get(REPEATED_INVOCATION):
            response = lambda_client.publish_version(**params)
            model["Version"] = response["Version"]
            model["Id"] = response["FunctionArn"]
            if model.get("ProvisionedConcurrencyConfig"):
                lambda_client.put_provisioned_concurrency_config(
                    FunctionName=model["FunctionName"],
                    Qualifier=model["Version"],
                    ProvisionedConcurrentExecutions=model["ProvisionedConcurrencyConfig"][
                        "ProvisionedConcurrentExecutions"
                    ],
                )
            ctx[REPEATED_INVOCATION] = True
            return ProgressEvent(
                status=OperationStatus.IN_PROGRESS,
                resource_model=model,
                custom_context=request.custom_context,
            )

        if model.get("ProvisionedConcurrencyConfig"):
            # Assumption: Ready provisioned concurrency implies the function version is ready
            provisioned_concurrency_config = lambda_client.get_provisioned_concurrency_config(
                FunctionName=model["FunctionName"],
                Qualifier=model["Version"],
            )
            if provisioned_concurrency_config["Status"] == "IN_PROGRESS":
                return ProgressEvent(
                    status=OperationStatus.IN_PROGRESS,
                    resource_model=model,
                    custom_context=request.custom_context,
                )
            elif provisioned_concurrency_config["Status"] == "READY":
                return ProgressEvent(
                    status=OperationStatus.SUCCESS,
                    resource_model=model,
                )
            else:
                return ProgressEvent(
                    status=OperationStatus.FAILED,
                    resource_model=model,
                    message="",
                    error_code="VersionStateFailure",  # TODO: not parity tested
                )
        else:
            version = lambda_client.get_function(FunctionName=model["Id"])
            if version["Configuration"]["State"] == "Pending":
                return ProgressEvent(
                    status=OperationStatus.IN_PROGRESS,
                    resource_model=model,
                    custom_context=request.custom_context,
                )
            elif version["Configuration"]["State"] == "Active":
                return ProgressEvent(
                    status=OperationStatus.SUCCESS,
                    resource_model=model,
                )
            else:
                return ProgressEvent(
                    status=OperationStatus.FAILED,
                    resource_model=model,
                    message="",
                    error_code="VersionStateFailure",  # TODO: not parity tested
                )