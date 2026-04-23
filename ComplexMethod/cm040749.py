def create(
        self,
        request: ResourceRequest[LambdaFunctionProperties],
    ) -> ProgressEvent[LambdaFunctionProperties]:
        """
        Create a new resource.

        Primary identifier fields:
          - /properties/FunctionName

        Required properties:
          - Code
          - Role

        Create-only properties:
          - /properties/FunctionName
          - /properties/PackageType
          - /properties/TenancyConfig

        Read-only properties:
          - /properties/Arn
          - /properties/SnapStartResponse
          - /properties/SnapStartResponse/ApplyOn
          - /properties/SnapStartResponse/OptimizationStatus

        IAM permissions required:
          - lambda:CreateFunction
          - lambda:GetFunction
          - lambda:PutFunctionConcurrency
          - iam:PassRole
          - s3:GetObject
          - s3:GetObjectVersion
          - ec2:DescribeSecurityGroups
          - ec2:DescribeSubnets
          - ec2:DescribeVpcs
          - elasticfilesystem:DescribeMountTargets
          - kms:CreateGrant
          - kms:Decrypt
          - kms:Encrypt
          - kms:GenerateDataKey
          - lambda:GetCodeSigningConfig
          - lambda:GetFunctionCodeSigningConfig
          - lambda:GetLayerVersion
          - lambda:GetRuntimeManagementConfig
          - lambda:PutRuntimeManagementConfig
          - lambda:TagResource
          - lambda:GetPolicy
          - lambda:PutFunctionRecursionConfig
          - lambda:GetFunctionRecursionConfig
          - lambda:PutFunctionScalingConfig
          - lambda:PassCapacityProvider

        """
        model = request.desired_state
        lambda_client = request.aws_client_factory.lambda_

        if not request.custom_context.get(REPEATED_INVOCATION):
            request.custom_context[REPEATED_INVOCATION] = True

            name = model.get("FunctionName")
            if not name:
                name = util.generate_default_name(request.stack_name, request.logical_resource_id)
                model["FunctionName"] = name

            kwargs = util.select_attributes(
                model,
                [
                    "Architectures",
                    "DeadLetterConfig",
                    "Description",
                    "FunctionName",
                    "Handler",
                    "ImageConfig",
                    "PackageType",
                    "Layers",
                    "MemorySize",
                    "Runtime",
                    "Role",
                    "Timeout",
                    "TracingConfig",
                    "VpcConfig",
                    "LoggingConfig",
                    "CapacityProviderConfig",
                ],
            )
            if "Timeout" in kwargs:
                kwargs["Timeout"] = int(kwargs["Timeout"])
            if "MemorySize" in kwargs:
                kwargs["MemorySize"] = int(kwargs["MemorySize"])
            if model_tags := model.get("Tags"):
                tags = {}
                for tag in model_tags:
                    tags[tag["Key"]] = tag["Value"]
                kwargs["Tags"] = tags

            # botocore/data/lambda/2015-03-31/service-2.json:1161 (EnvironmentVariableValue)
            # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-lambda-function-environment.html
            if "Environment" in model:
                environment_variables = model["Environment"].get("Variables", {})
                kwargs["Environment"] = {
                    "Variables": {k: str(v) for k, v in environment_variables.items()}
                }

            kwargs["Code"] = _get_lambda_code_param(model)

            # For managed instance lambdas, we publish them immediately
            if "CapacityProviderConfig" in kwargs:
                kwargs["Publish"] = True
                kwargs["PublishTo"] = "LATEST_PUBLISHED"

            create_response = lambda_client.create_function(**kwargs)
            # TODO: if version is in the schema, just put it in the model instead of the custom context
            request.custom_context["Version"] = create_response["Version"]  # $LATEST.PUBLISHED
            model["Arn"] = create_response["FunctionArn"]

        if request.custom_context.get("Version") == "$LATEST.PUBLISHED":
            # for managed instance lambdas, we need to wait until the version is published & active
            get_fn_response = lambda_client.get_function(
                FunctionName=model["FunctionName"], Qualifier=request.custom_context["Version"]
            )
        else:
            get_fn_response = lambda_client.get_function(FunctionName=model["Arn"])

        match get_fn_response["Configuration"]["State"]:
            # TODO: explicitly handle new ActiveNonInvocable state?
            case "Pending":
                return ProgressEvent(
                    status=OperationStatus.IN_PROGRESS,
                    resource_model=model,
                    custom_context=request.custom_context,
                )
            case "Active":
                return ProgressEvent(status=OperationStatus.SUCCESS, resource_model=model)
            case "Inactive":
                # This might happen when setting LAMBDA_KEEPALIVE_MS=0
                return ProgressEvent(status=OperationStatus.SUCCESS, resource_model=model)
            case "Failed":
                return ProgressEvent(
                    status=OperationStatus.FAILED,
                    resource_model=model,
                    error_code=get_fn_response["Configuration"].get("StateReasonCode", "unknown"),
                    message=get_fn_response["Configuration"].get("StateReason", "unknown"),
                )
            case unknown_state:  # invalid state, should technically never happen
                return ProgressEvent(
                    status=OperationStatus.FAILED,
                    resource_model=model,
                    error_code="InternalException",
                    message=f"Invalid state returned: {unknown_state}",
                )