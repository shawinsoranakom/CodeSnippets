def test_create_subnet_with_custom_id_and_vpc_id(self, cleanups, aws_client, create_vpc):
        custom_subnet_id = random_subnet_id()
        custom_vpc_id = random_vpc_id()

        # Create the VPC with the custom ID.
        vpc: dict = create_vpc(
            cidr_block="10.0.0.0/16",
            tag_specifications=[
                {
                    "ResourceType": "vpc",
                    "Tags": [
                        {"Key": TAG_KEY_CUSTOM_ID, "Value": custom_vpc_id},
                    ],
                }
            ],
        )
        assert vpc["Vpc"]["VpcId"] == custom_vpc_id

        # Check if subnet ID matches the custom ID
        subnet: dict = aws_client.ec2.create_subnet(
            VpcId=custom_vpc_id,
            CidrBlock="10.0.0.0/24",
            TagSpecifications=[
                {
                    "ResourceType": "subnet",
                    "Tags": [
                        {"Key": TAG_KEY_CUSTOM_ID, "Value": custom_subnet_id},
                    ],
                }
            ],
        )
        cleanups.append(lambda: aws_client.ec2.delete_subnet(SubnetId=custom_subnet_id))
        assert subnet["Subnet"]["SubnetId"] == custom_subnet_id

        # Check if the custom ID is present in the describe_subnets response as well
        subnet: dict = aws_client.ec2.describe_subnets(
            SubnetIds=[custom_subnet_id],
        )["Subnets"][0]
        assert subnet["SubnetId"] == custom_subnet_id
        assert subnet["VpcId"] == custom_vpc_id
        assert len(subnet["Tags"]) == 1
        assert subnet["Tags"][0]["Key"] == TAG_KEY_CUSTOM_ID
        assert subnet["Tags"][0]["Value"] == custom_subnet_id