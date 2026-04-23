def modify_subnet_attribute(
        self, context: RequestContext, request: ModifySubnetAttributeRequest
    ) -> None:
        try:
            return call_moto(context)
        except Exception as e:
            if not isinstance(e, ResponseParserError) and "InvalidParameterValue" not in str(e):
                raise

            backend = get_ec2_backend(context.account_id, context.region)

            # fix setting subnet attributes currently not supported upstream
            subnet_id = request["SubnetId"]
            host_type = request.get("PrivateDnsHostnameTypeOnLaunch")
            a_record_on_launch = request.get("EnableResourceNameDnsARecordOnLaunch")
            aaaa_record_on_launch = request.get("EnableResourceNameDnsAAAARecordOnLaunch")
            enable_dns64 = request.get("EnableDns64")

            if host_type:
                attr_name = camelcase_to_underscores("PrivateDnsNameOptionsOnLaunch")
                value = {"HostnameType": host_type}
                backend.modify_subnet_attribute(subnet_id, attr_name, value)
            ## explicitly checking None value as this could contain a False value
            if aaaa_record_on_launch is not None:
                attr_name = camelcase_to_underscores("PrivateDnsNameOptionsOnLaunch")
                value = {"EnableResourceNameDnsAAAARecord": aaaa_record_on_launch["Value"]}
                backend.modify_subnet_attribute(subnet_id, attr_name, value)
            if a_record_on_launch is not None:
                attr_name = camelcase_to_underscores("PrivateDnsNameOptionsOnLaunch")
                value = {"EnableResourceNameDnsARecord": a_record_on_launch["Value"]}
                backend.modify_subnet_attribute(subnet_id, attr_name, value)
            if enable_dns64 is not None:
                attr_name = camelcase_to_underscores("EnableDns64")
                backend.modify_subnet_attribute(subnet_id, attr_name, enable_dns64["Value"])