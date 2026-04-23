def update(
        self,
        request: ResourceRequest[LambdaFunctionProperties],
    ) -> ProgressEvent[LambdaFunctionProperties]:
        """
        Update a resource

        IAM permissions required:
          - lambda:DeleteFunctionConcurrency
          - lambda:GetFunction
          - lambda:PutFunctionConcurrency
          - lambda:TagResource
          - lambda:UntagResource
          - lambda:UpdateFunctionConfiguration
          - lambda:UpdateFunctionCode
          - iam:PassRole
          - s3:GetObject
          - s3:GetObjectVersion
          - ec2:DescribeSecurityGroups
          - ec2:DescribeSubnets
          - ec2:DescribeVpcs
          - elasticfilesystem:DescribeMountTargets
          - kms:CreateGrant
          - kms:Decrypt
          - kms:GenerateDataKey
          - lambda:GetRuntimeManagementConfig
          - lambda:PutRuntimeManagementConfig
          - lambda:PutFunctionCodeSigningConfig
          - lambda:DeleteFunctionCodeSigningConfig
          - lambda:GetCodeSigningConfig
          - lambda:GetFunctionCodeSigningConfig
          - lambda:PutFunctionRecursionConfig
          - lambda:GetFunctionRecursionConfig
          - lambda:PutFunctionScalingConfig
          - lambda:PublishVersion
          - lambda:PassCapacityProvider
        """
        client = request.aws_client_factory.lambda_

        # TODO: handle defaults properly
        old_name = request.previous_state["FunctionName"]
        new_name = request.desired_state.get("FunctionName")
        if new_name and old_name != new_name:
            # replacement (!) => shouldn't be handled here but in the engine
            self.delete(request)
            return self.create(request)

        config_keys = [
            "Description",
            "DeadLetterConfig",
            "Environment",
            "Handler",
            "ImageConfig",
            "Layers",
            "MemorySize",
            "Role",
            "Runtime",
            "Timeout",
            "TracingConfig",
            "VpcConfig",
            "LoggingConfig",
            "CapacityProviderConfig",
        ]
        update_config_props = util.select_attributes(request.desired_state, config_keys)
        function_name = request.previous_state["FunctionName"]
        update_config_props["FunctionName"] = function_name

        if "Timeout" in update_config_props:
            update_config_props["Timeout"] = int(update_config_props["Timeout"])
        if "MemorySize" in update_config_props:
            update_config_props["MemorySize"] = int(update_config_props["MemorySize"])
        if "Code" in request.desired_state:
            code = request.desired_state["Code"] or {}
            if not code.get("ZipFile"):
                request.logger.debug(
                    'Updating code for Lambda "%s" from location: %s', function_name, code
                )
            code = _get_lambda_code_param(
                request.desired_state,
                _include_arch=True,
            )
            client.update_function_code(FunctionName=function_name, **code)
            client.get_waiter("function_updated_v2").wait(FunctionName=function_name)
        if "Environment" in update_config_props:
            environment_variables = update_config_props["Environment"].get("Variables", {})
            update_config_props["Environment"]["Variables"] = {
                k: str(v) for k, v in environment_variables.items()
            }
        client.update_function_configuration(**update_config_props)
        client.get_waiter("function_updated_v2").wait(FunctionName=function_name)
        return ProgressEvent(
            status=OperationStatus.SUCCESS,
            resource_model={**request.previous_state, **request.desired_state},
        )