def modify_vpc_endpoint(
        self,
        context: RequestContext,
        vpc_endpoint_id: VpcEndpointId,
        dry_run: Boolean = None,
        reset_policy: Boolean = None,
        policy_document: String = None,
        add_route_table_ids: VpcEndpointRouteTableIdList = None,
        remove_route_table_ids: VpcEndpointRouteTableIdList = None,
        add_subnet_ids: VpcEndpointSubnetIdList = None,
        remove_subnet_ids: VpcEndpointSubnetIdList = None,
        add_security_group_ids: VpcEndpointSecurityGroupIdList = None,
        remove_security_group_ids: VpcEndpointSecurityGroupIdList = None,
        ip_address_type: IpAddressType = None,
        dns_options: DnsOptionsSpecification = None,
        private_dns_enabled: Boolean = None,
        subnet_configurations: SubnetConfigurationsList = None,
        **kwargs,
    ) -> ModifyVpcEndpointResult:
        backend = get_ec2_backend(context.account_id, context.region)

        vpc_endpoint = backend.vpc_end_points.get(vpc_endpoint_id)
        if not vpc_endpoint:
            raise InvalidVpcEndPointIdError(vpc_endpoint_id)

        if policy_document is not None:
            vpc_endpoint.policy_document = policy_document

        if add_route_table_ids is not None:
            vpc_endpoint.route_table_ids.extend(add_route_table_ids)

        if remove_route_table_ids is not None:
            vpc_endpoint.route_table_ids = [
                id_ for id_ in vpc_endpoint.route_table_ids if id_ not in remove_route_table_ids
            ]

        if add_subnet_ids is not None:
            vpc_endpoint.subnet_ids.extend(add_subnet_ids)

        if remove_subnet_ids is not None:
            vpc_endpoint.subnet_ids = [
                id_ for id_ in vpc_endpoint.subnet_ids if id_ not in remove_subnet_ids
            ]

        if private_dns_enabled is not None:
            vpc_endpoint.private_dns_enabled = private_dns_enabled

        return ModifyVpcEndpointResult(Return=True)