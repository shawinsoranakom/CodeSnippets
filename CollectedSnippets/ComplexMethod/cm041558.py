def test_create_security_group_with_custom_id(
        self, cleanups, aws_client, create_vpc, strategy, account_id, region_name, default_vpc
    ):
        custom_id = random_security_group_id()
        group_name = f"test-security-group-{short_uid()}"
        vpc_id = None

        # Create necessary VPC resource
        if default_vpc:
            vpc: dict = aws_client.ec2.describe_vpcs(
                Filters=[{"Name": "is-default", "Values": ["true"]}]
            )["Vpcs"][0]
            vpc_id = vpc["VpcId"]
        else:
            vpc: dict = create_vpc(
                cidr_block="10.0.0.0/24",
                tag_specifications=[],
            )
            vpc_id = vpc["Vpc"]["VpcId"]

        def _create_security_group() -> dict:
            req_kwargs = {"Description": "Test security group", "GroupName": group_name}
            if not default_vpc:
                # vpc_id does not need to be provided for default vpc
                req_kwargs["VpcId"] = vpc_id
            if strategy == "tag":
                req_kwargs["TagSpecifications"] = [
                    {
                        "ResourceType": "security-group",
                        "Tags": [{"Key": TAG_KEY_CUSTOM_ID, "Value": custom_id}],
                    }
                ]
                return aws_client.ec2.create_security_group(**req_kwargs)
            else:
                with localstack_id_manager.custom_id(
                    SecurityGroupIdentifier(
                        account_id=account_id,
                        region=region_name,
                        vpc_id=vpc_id,
                        group_name=group_name,
                    ),
                    custom_id,
                ):
                    return aws_client.ec2.create_security_group(**req_kwargs)

        security_group: dict = _create_security_group()

        cleanups.append(lambda: aws_client.ec2.delete_security_group(GroupId=custom_id))
        # Check if security group ID matches the custom ID
        assert security_group["GroupId"] == custom_id, (
            f"Security group ID does not match custom ID: {security_group}"
        )

        # Check if the custom ID is present in the describe_security_groups response as well
        security_groups: dict = aws_client.ec2.describe_security_groups(
            GroupIds=[custom_id],
        )["SecurityGroups"]

        # Get security group that match a given VPC id
        security_group = next((sg for sg in security_groups if sg["VpcId"] == vpc_id), None)
        assert security_group["GroupId"] == custom_id
        if strategy == "tag":
            assert len(security_group["Tags"]) == 1
            assert security_group["Tags"][0]["Key"] == TAG_KEY_CUSTOM_ID
            assert security_group["Tags"][0]["Value"] == custom_id

        # Check if a duplicate custom ID exception is thrown if we try to recreate the security group with the same custom ID
        with pytest.raises(ClientError) as e:
            _create_security_group()

        assert e.value.response["ResponseMetadata"]["HTTPStatusCode"] == 400
        assert e.value.response["Error"]["Code"] == "InvalidSecurityGroupId.DuplicateCustomId"