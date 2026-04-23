def ec2_create_vpc(
        fn: ec2_models.vpcs.VPCBackend.create_vpc,
        self: ec2_models.vpcs.VPCBackend,
        cidr_block: str,
        *args,
        tags: list[dict[str, str]] | None = None,
        is_default: bool = False,
        **kwargs,
    ):
        resource_identifier = VpcIdentifier(self.account_id, self.region_name, cidr_block)
        custom_id = resource_identifier.generate(tags=tags)

        # Check if custom id is unique
        if custom_id and custom_id in self.vpcs:
            raise InvalidVpcDuplicateCustomIdError(custom_id)

        # Generate VPC with moto library
        result: ec2_models.vpcs.VPC = fn(
            self, cidr_block, *args, tags=tags, is_default=is_default, **kwargs
        )
        vpc_id = result.id

        if custom_id:
            # Remove security group associated with unique non-custom VPC ID
            default = self.get_security_group_from_name("default", vpc_id=vpc_id)
            if not default:
                self.delete_security_group(
                    name="default",
                    vpc_id=vpc_id,
                )

            # Delete route table if only main route table remains.
            for route_table in self.describe_route_tables(filters={"vpc-id": vpc_id}):
                self.delete_route_table(route_table.id)  # type: ignore[attr-defined]

            # Remove the VPC from the default dict and add it back with the custom id
            self.vpcs.pop(vpc_id)
            old_id = result.id
            result.id = custom_id
            self.vpcs[custom_id] = result

            # Tags are not stored in the VPC object, but instead stored in a separate
            # dict in the EC2 backend, keyed by VPC id.  That therefore requires
            # updating as well.
            if old_id in self.tags:
                self.tags[custom_id] = self.tags.pop(old_id)

            # Create default network ACL, route table, and security group for custom ID VPC
            self.create_route_table(
                vpc_id=custom_id,
                main=True,
            )
            self.create_network_acl(
                vpc_id=custom_id,
                default=True,
            )
            # Associate default security group with custom ID VPC
            if not default:
                self.create_security_group(
                    name="default",
                    description="default VPC security group",
                    vpc_id=custom_id,
                    is_default=is_default,
                )

        return result