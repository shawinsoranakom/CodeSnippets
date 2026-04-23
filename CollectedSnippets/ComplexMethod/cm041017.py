def generate_subnet_read_payload(
    ec2_client, schema, subnet_ids: list[str] | None = None
) -> list[EC2SubnetProperties]:
    kwargs = {}
    if subnet_ids:
        kwargs["SubnetIds"] = subnet_ids
    subnets = ec2_client.describe_subnets(**kwargs)["Subnets"]

    models = []
    for subnet in subnets:
        subnet_id = subnet["SubnetId"]

        model = EC2SubnetProperties(**util.select_attributes(subnet, schema))

        if "Tags" not in model:
            model["Tags"] = []

        if "EnableDns64" not in model:
            model["EnableDns64"] = False

        private_dns_name_options = model.setdefault("PrivateDnsNameOptionsOnLaunch", {})

        if "HostnameType" not in private_dns_name_options:
            private_dns_name_options["HostnameType"] = "ip-name"

        optional_bool_attrs = ["EnableResourceNameDnsAAAARecord", "EnableResourceNameDnsARecord"]
        for attr in optional_bool_attrs:
            if attr not in private_dns_name_options:
                private_dns_name_options[attr] = False

        network_acl_associations = ec2_client.describe_network_acls(
            Filters=[{"Name": "association.subnet-id", "Values": [subnet_id]}]
        )
        model["NetworkAclAssociationId"] = network_acl_associations["NetworkAcls"][0][
            "NetworkAclId"
        ]
        models.append(model)

    return models