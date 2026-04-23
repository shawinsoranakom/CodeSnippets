def test_describe_vpc_endpoints_with_filter(self, aws_client, region_name):
        vpc = aws_client.ec2.create_vpc(CidrBlock="10.0.0.0/16")
        vpc_id = vpc["Vpc"]["VpcId"]

        # test filter of Gateway endpoint services
        vpc_endpoint_gateway_services = aws_client.ec2.describe_vpc_endpoint_services(
            Filters=[
                {"Name": "service-type", "Values": ["Gateway"]},
            ],
        )

        assert 200 == vpc_endpoint_gateway_services["ResponseMetadata"]["HTTPStatusCode"]
        services = vpc_endpoint_gateway_services["ServiceNames"]
        assert 2 == len(services)
        assert f"com.amazonaws.{region_name}.dynamodb" in services
        assert f"com.amazonaws.{region_name}.s3" in services

        # test filter of Interface endpoint services
        vpc_endpoint_interface_services = aws_client.ec2.describe_vpc_endpoint_services(
            Filters=[
                {"Name": "service-type", "Values": ["Interface"]},
            ],
        )

        assert 200 == vpc_endpoint_interface_services["ResponseMetadata"]["HTTPStatusCode"]
        services = vpc_endpoint_interface_services["ServiceNames"]
        assert len(services) > 0
        assert (
            f"com.amazonaws.{region_name}.s3" in services
        )  # S3 is both gateway and interface service
        assert f"com.amazonaws.{region_name}.kinesis-firehose" in services

        # test filter that does not exist
        vpc_endpoint_interface_services = aws_client.ec2.describe_vpc_endpoint_services(
            Filters=[
                {"Name": "service-type", "Values": ["fake"]},
            ],
        )

        assert 200 == vpc_endpoint_interface_services["ResponseMetadata"]["HTTPStatusCode"]
        services = vpc_endpoint_interface_services["ServiceNames"]
        assert len(services) == 0

        # clean up
        aws_client.ec2.delete_vpc(VpcId=vpc_id)