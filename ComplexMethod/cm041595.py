def test_associate_vpc_with_hosted_zone(
        self, cleanups, hosted_zone, aws_client, account_id, region_name
    ):
        # create VPCs
        vpc1 = aws_client.ec2.create_vpc(CidrBlock="10.113.0.0/24")
        cleanups.append(lambda: aws_client.ec2.delete_vpc(VpcId=vpc1["Vpc"]["VpcId"]))
        vpc1_id = vpc1["Vpc"]["VpcId"]
        vpc2 = aws_client.ec2.create_vpc(CidrBlock="10.114.0.0/24")
        cleanups.append(lambda: aws_client.ec2.delete_vpc(VpcId=vpc2["Vpc"]["VpcId"]))
        vpc2_id = vpc2["Vpc"]["VpcId"]

        name = "zone123"
        response = hosted_zone(
            Name=name,
            HostedZoneConfig={
                "PrivateZone": True,
                "Comment": "test",
            },
            VPC={"VPCId": vpc1_id, "VPCRegion": region_name},
        )
        zone_id = response["HostedZone"]["Id"]
        zone_id = zone_id.replace("/hostedzone/", "")

        # associate zone with VPC
        vpc_region = region_name
        for vpc_id in [vpc2_id]:
            result = aws_client.route53.associate_vpc_with_hosted_zone(
                HostedZoneId=zone_id,
                VPC={"VPCRegion": vpc_region, "VPCId": vpc_id},
                Comment="test 123",
            )
            assert result["ChangeInfo"].get("Id")

        cleanups.append(
            lambda: aws_client.route53.disassociate_vpc_from_hosted_zone(
                HostedZoneId=zone_id, VPC={"VPCRegion": vpc_region, "VPCId": vpc1_id}
            )
        )

        # list zones by VPC
        result = aws_client.route53.list_hosted_zones_by_vpc(VPCId=vpc1_id, VPCRegion=vpc_region)[
            "HostedZoneSummaries"
        ]
        expected = {
            "HostedZoneId": zone_id,
            "Name": f"{name}.",
            "Owner": {"OwningAccount": account_id},
        }
        assert expected in result

        # list zones by name
        result = aws_client.route53.list_hosted_zones_by_name(DNSName=name).get("HostedZones")
        assert result[0]["Name"] == "zone123."
        result = aws_client.route53.list_hosted_zones_by_name(DNSName=f"{name}.").get("HostedZones")
        assert result[0]["Name"] == "zone123."

        # assert that VPC is attached in Zone response
        result = aws_client.route53.get_hosted_zone(Id=zone_id)
        for vpc_id in [vpc1_id, vpc2_id]:
            assert {"VPCRegion": vpc_region, "VPCId": vpc_id} in result["VPCs"]

        # disassociate
        aws_client.route53.disassociate_vpc_from_hosted_zone(
            HostedZoneId=zone_id,
            VPC={"VPCRegion": vpc_region, "VPCId": vpc2_id},
            Comment="test2",
        )
        assert response["ResponseMetadata"]["HTTPStatusCode"] in [200, 201]
        # subsequent call (after disassociation) should fail with 404 error
        with pytest.raises(ClientError):
            aws_client.route53.disassociate_vpc_from_hosted_zone(
                HostedZoneId=zone_id,
                VPC={"VPCRegion": vpc_region, "VPCId": vpc2_id},
            )