def create_hosted_zone(
        self,
        context: RequestContext,
        name: DNSName,
        caller_reference: Nonce,
        vpc: VPC = None,
        hosted_zone_config: HostedZoneConfig = None,
        delegation_set_id: ResourceId = None,
        **kwargs,
    ) -> CreateHostedZoneResponse:
        # private hosted zones cannot be created in a VPC that does not exist
        # check that the VPC exists
        if vpc:
            vpc_id = vpc.get("VPCId")
            vpc_region = vpc.get("VPCRegion")
            if not vpc_id or not vpc_region:
                raise Exception(
                    "VPCId and VPCRegion must be specified when creating a private hosted zone"
                )
            try:
                connect_to(
                    aws_access_key_id=context.account_id, region_name=vpc_region
                ).ec2.describe_vpcs(VpcIds=[vpc_id])
            except ClientError as e:
                if e.response.get("Error", {}).get("Code") == "InvalidVpcID.NotFound":
                    raise InvalidVPCId("The VPC ID is invalid.", sender_fault=True) from e
                raise e

        response = call_moto(context)

        # moto does not populate the VPC struct of the response if creating a private hosted zone
        if (
            hosted_zone_config
            and hosted_zone_config.get("PrivateZone", False)
            and "VPC" in response
            and vpc
        ):
            response["VPC"]["VPCId"] = response["VPC"]["VPCId"] or vpc.get("VPCId", "")
            response["VPC"]["VPCRegion"] = response["VPC"]["VPCRegion"] or vpc.get("VPCRegion", "")

        return response