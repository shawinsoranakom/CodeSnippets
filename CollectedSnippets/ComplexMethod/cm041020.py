def create(
        self,
        request: ResourceRequest[EC2DHCPOptionsProperties],
    ) -> ProgressEvent[EC2DHCPOptionsProperties]:
        """
        Create a new resource.

        Primary identifier fields:
          - /properties/DhcpOptionsId



        Create-only properties:
          - /properties/NetbiosNameServers
          - /properties/NetbiosNodeType
          - /properties/NtpServers
          - /properties/DomainName
          - /properties/DomainNameServers

        Read-only properties:
          - /properties/DhcpOptionsId

        IAM permissions required:
          - ec2:CreateDhcpOptions
          - ec2:DescribeDhcpOptions
          - ec2:CreateTags

        """
        model = request.desired_state

        dhcp_configurations = []
        if model.get("DomainName"):
            dhcp_configurations.append({"Key": "domain-name", "Values": [model["DomainName"]]})
        if model.get("DomainNameServers"):
            dhcp_configurations.append(
                {"Key": "domain-name-servers", "Values": model["DomainNameServers"]}
            )
        if model.get("NetbiosNameServers"):
            dhcp_configurations.append(
                {"Key": "netbios-name-servers", "Values": model["NetbiosNameServers"]}
            )
        if model.get("NetbiosNodeType"):
            dhcp_configurations.append(
                {"Key": "netbios-node-type", "Values": [str(model["NetbiosNodeType"])]}
            )
        if model.get("NtpServers"):
            dhcp_configurations.append({"Key": "ntp-servers", "Values": model["NtpServers"]})

        create_params = {
            "DhcpConfigurations": dhcp_configurations,
        }
        if model.get("Tags"):
            tags = [{"Key": str(tag["Key"]), "Value": str(tag["Value"])} for tag in model["Tags"]]
        else:
            tags = []

        default_tags = [
            {"Key": "aws:cloudformation:logical-id", "Value": request.logical_resource_id},
            {"Key": "aws:cloudformation:stack-id", "Value": request.stack_id},
            {"Key": "aws:cloudformation:stack-name", "Value": request.stack_name},
        ]

        create_params["TagSpecifications"] = [
            {"ResourceType": "dhcp-options", "Tags": (tags + default_tags)}
        ]

        result = request.aws_client_factory.ec2.create_dhcp_options(**create_params)
        model["DhcpOptionsId"] = result["DhcpOptions"]["DhcpOptionsId"]

        return ProgressEvent(status=OperationStatus.SUCCESS, resource_model=model)