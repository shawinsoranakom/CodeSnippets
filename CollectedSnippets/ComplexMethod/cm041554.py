def test_create_vpc_endpoint(self, cleanups, aws_client):
        vpc = aws_client.ec2.create_vpc(CidrBlock="10.0.0.0/16")
        cleanups.append(lambda: aws_client.ec2.delete_vpc(VpcId=vpc["Vpc"]["VpcId"]))
        subnet = aws_client.ec2.create_subnet(VpcId=vpc["Vpc"]["VpcId"], CidrBlock="10.0.0.0/24")
        cleanups.append(lambda: aws_client.ec2.delete_subnet(SubnetId=subnet["Subnet"]["SubnetId"]))
        route_table = aws_client.ec2.create_route_table(VpcId=vpc["Vpc"]["VpcId"])
        cleanups.append(
            lambda: aws_client.ec2.delete_route_table(
                RouteTableId=route_table["RouteTable"]["RouteTableId"]
            )
        )

        # test without any endpoint type specified
        vpc_endpoint = aws_client.ec2.create_vpc_endpoint(
            VpcId=vpc["Vpc"]["VpcId"],
            ServiceName="com.amazonaws.us-east-1.s3",
            RouteTableIds=[route_table["RouteTable"]["RouteTableId"]],
        )
        cleanups.append(
            lambda: aws_client.ec2.delete_vpc_endpoints(
                VpcEndpointIds=[vpc_endpoint["VpcEndpoint"]["VpcEndpointId"]]
            )
        )

        assert "com.amazonaws.us-east-1.s3" == vpc_endpoint["VpcEndpoint"]["ServiceName"]
        assert (
            route_table["RouteTable"]["RouteTableId"]
            == vpc_endpoint["VpcEndpoint"]["RouteTableIds"][0]
        )
        assert vpc["Vpc"]["VpcId"] == vpc_endpoint["VpcEndpoint"]["VpcId"]
        assert 0 == len(vpc_endpoint["VpcEndpoint"]["DnsEntries"])

        # test with any endpoint type as gateway
        vpc_endpoint = aws_client.ec2.create_vpc_endpoint(
            VpcId=vpc["Vpc"]["VpcId"],
            ServiceName="com.amazonaws.us-east-1.s3",
            RouteTableIds=[route_table["RouteTable"]["RouteTableId"]],
            VpcEndpointType="gateway",
        )
        cleanups.append(
            lambda: aws_client.ec2.delete_vpc_endpoints(
                VpcEndpointIds=[vpc_endpoint["VpcEndpoint"]["VpcEndpointId"]]
            )
        )

        assert "com.amazonaws.us-east-1.s3" == vpc_endpoint["VpcEndpoint"]["ServiceName"]
        assert (
            route_table["RouteTable"]["RouteTableId"]
            == vpc_endpoint["VpcEndpoint"]["RouteTableIds"][0]
        )
        assert vpc["Vpc"]["VpcId"] == vpc_endpoint["VpcEndpoint"]["VpcId"]
        assert 0 == len(vpc_endpoint["VpcEndpoint"]["DnsEntries"])

        # test with endpoint type as interface
        vpc_endpoint = aws_client.ec2.create_vpc_endpoint(
            VpcId=vpc["Vpc"]["VpcId"],
            ServiceName="com.amazonaws.us-east-1.s3",
            SubnetIds=[subnet["Subnet"]["SubnetId"]],
            VpcEndpointType="interface",
        )
        cleanups.append(
            lambda: aws_client.ec2.delete_vpc_endpoints(
                VpcEndpointIds=[vpc_endpoint["VpcEndpoint"]["VpcEndpointId"]]
            )
        )

        assert "com.amazonaws.us-east-1.s3" == vpc_endpoint["VpcEndpoint"]["ServiceName"]
        assert subnet["Subnet"]["SubnetId"] == vpc_endpoint["VpcEndpoint"]["SubnetIds"][0]
        assert vpc["Vpc"]["VpcId"] == vpc_endpoint["VpcEndpoint"]["VpcId"]
        assert len(vpc_endpoint["VpcEndpoint"]["DnsEntries"]) > 0