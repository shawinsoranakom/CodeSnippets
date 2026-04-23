def create(
        self,
        request: ResourceRequest[EC2VPCEndpointProperties],
    ) -> ProgressEvent[EC2VPCEndpointProperties]:
        """
        Create a new resource.

        Primary identifier fields:
          - /properties/Id

        Required properties:
          - VpcId
          - ServiceName

        Create-only properties:
          - /properties/ServiceName
          - /properties/VpcEndpointType
          - /properties/VpcId

        Read-only properties:
          - /properties/NetworkInterfaceIds
          - /properties/CreationTimestamp
          - /properties/DnsEntries
          - /properties/Id

        IAM permissions required:
          - ec2:CreateVpcEndpoint
          - ec2:DescribeVpcEndpoints

        """
        model = request.desired_state
        ec2 = request.aws_client_factory.ec2

        create_params = util.select_attributes(
            model=model,
            params=[
                "PolicyDocument",
                "PrivateDnsEnabled",
                "RouteTableIds",
                "SecurityGroupIds",
                "ServiceName",
                "SubnetIds",
                "VpcEndpointType",
                "VpcId",
            ],
        )

        if policy := model.get("PolicyDocument"):
            create_params["PolicyDocument"] = json.dumps(policy)

        if not request.custom_context.get(REPEATED_INVOCATION):
            response = ec2.create_vpc_endpoint(**create_params)
            model["Id"] = response["VpcEndpoint"]["VpcEndpointId"]
            model["DnsEntries"] = response["VpcEndpoint"]["DnsEntries"]
            model["CreationTimestamp"] = response["VpcEndpoint"]["CreationTimestamp"].isoformat()
            model["NetworkInterfaceIds"] = response["VpcEndpoint"]["NetworkInterfaceIds"]
            model["VpcEndpointType"] = model.get("VpcEndpointType") or "Gateway"
            model["PrivateDnsEnabled"] = bool(model.get("VpcEndpointType", False))

            request.custom_context[REPEATED_INVOCATION] = True
            return ProgressEvent(
                status=OperationStatus.IN_PROGRESS,
                resource_model=model,
                custom_context=request.custom_context,
            )

        response = ec2.describe_vpc_endpoints(VpcEndpointIds=[model["Id"]])
        if not response["VpcEndpoints"]:
            return ProgressEvent(
                status=OperationStatus.FAILED,
                resource_model=model,
                custom_context=request.custom_context,
                message="Resource not found after creation",
            )

        state = response["VpcEndpoints"][0][
            "State"
        ].lower()  # API specifies capital but lowercase is returned
        match state:
            case "available":
                return ProgressEvent(status=OperationStatus.SUCCESS, resource_model=model)
            case "pending":
                return ProgressEvent(status=OperationStatus.IN_PROGRESS, resource_model=model)
            case "pendingacceptance":
                return ProgressEvent(status=OperationStatus.IN_PROGRESS, resource_model=model)
            case _:
                return ProgressEvent(
                    status=OperationStatus.FAILED,
                    resource_model=model,
                    message=f"Invalid state '{state}' for resource",
                )