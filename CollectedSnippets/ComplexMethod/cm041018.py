def create(
        self,
        request: ResourceRequest[EC2SubnetProperties],
    ) -> ProgressEvent[EC2SubnetProperties]:
        """
        Create a new resource.

        Primary identifier fields:
          - /properties/SubnetId

        Required properties:
          - VpcId

        Create-only properties:
          - /properties/VpcId
          - /properties/AvailabilityZone
          - /properties/AvailabilityZoneId
          - /properties/CidrBlock
          - /properties/OutpostArn
          - /properties/Ipv6Native

        Read-only properties:
          - /properties/NetworkAclAssociationId
          - /properties/SubnetId
          - /properties/Ipv6CidrBlocks

        IAM permissions required:
          - ec2:DescribeSubnets
          - ec2:CreateSubnet
          - ec2:CreateTags
          - ec2:ModifySubnetAttribute

        """
        model = request.desired_state
        ec2 = request.aws_client_factory.ec2

        params = util.select_attributes(
            model,
            [
                "AvailabilityZone",
                "AvailabilityZoneId",
                "CidrBlock",
                "Ipv6CidrBlock",
                "Ipv6Native",
                "OutpostArn",
                "VpcId",
            ],
        )
        if model.get("Tags"):
            tags = [{"ResourceType": "subnet", "Tags": model.get("Tags")}]
            params["TagSpecifications"] = tags

        response = ec2.create_subnet(**params)
        model["SubnetId"] = response["Subnet"]["SubnetId"]
        bool_attrs = [
            "AssignIpv6AddressOnCreation",
            "EnableDns64",
            "MapPublicIpOnLaunch",
        ]
        custom_attrs = bool_attrs + ["PrivateDnsNameOptionsOnLaunch"]
        if not any(attr in model for attr in custom_attrs):
            return ProgressEvent(
                status=OperationStatus.SUCCESS,
                resource_model=model,
                custom_context=request.custom_context,
            )

        # update boolean attributes
        for attr in bool_attrs:
            if attr in model:
                kwargs = {attr: {"Value": str_to_bool(model[attr])}}
                ec2.modify_subnet_attribute(SubnetId=model["SubnetId"], **kwargs)

        # determine DNS hostname type on launch
        dns_options = model.get("PrivateDnsNameOptionsOnLaunch")
        if dns_options:
            if isinstance(dns_options, str):
                dns_options = json.loads(dns_options)
            if dns_options.get("HostnameType"):
                ec2.modify_subnet_attribute(
                    SubnetId=model["SubnetId"],
                    PrivateDnsHostnameTypeOnLaunch=dns_options.get("HostnameType"),
                )
        return ProgressEvent(
            status=OperationStatus.SUCCESS,
            resource_model=model,
            custom_context=request.custom_context,
        )