def test_create_vpc_with_custom_id(self, aws_client, create_vpc):
        custom_id = random_vpc_id()

        # Check if the custom ID is present
        vpc: dict = create_vpc(
            cidr_block="10.0.0.0/16",
            tag_specifications=[
                {
                    "ResourceType": "vpc",
                    "Tags": [
                        {"Key": TAG_KEY_CUSTOM_ID, "Value": custom_id},
                    ],
                }
            ],
        )
        assert vpc["Vpc"]["VpcId"] == custom_id

        # Check if the custom ID is present in the describe_vpcs response as well
        vpc: dict = aws_client.ec2.describe_vpcs(VpcIds=[custom_id])["Vpcs"][0]
        assert vpc["VpcId"] == custom_id
        assert len(vpc["Tags"]) == 1
        assert vpc["Tags"][0]["Key"] == TAG_KEY_CUSTOM_ID
        assert vpc["Tags"][0]["Value"] == custom_id

        # Check if an duplicate custom ID exception is thrown if we try to recreate the VPC with the same custom ID
        with pytest.raises(ClientError) as e:
            create_vpc(
                cidr_block="10.0.0.0/16",
                tag_specifications=[
                    {
                        "ResourceType": "vpc",
                        "Tags": [
                            {"Key": TAG_KEY_CUSTOM_ID, "Value": custom_id},
                        ],
                    }
                ],
            )

        assert e.value.response["ResponseMetadata"]["HTTPStatusCode"] == 400
        assert e.value.response["Error"]["Code"] == "InvalidVpc.DuplicateCustomId"