def ec2_create_subnet(
        fn: ec2_models.subnets.SubnetBackend.create_subnet,
        self: ec2_models.subnets.SubnetBackend,
        *args,
        tags: dict[str, str] | None = None,
        **kwargs,
    ):
        # Patch this method so that we can create a subnet with a specific "custom"
        # ID.  The custom ID that we will use is contained within a special tag.
        vpc_id: str = args[0] if len(args) >= 1 else kwargs["vpc_id"]
        cidr_block: str = args[1] if len(args) >= 1 else kwargs["cidr_block"]
        resource_identifier = SubnetIdentifier(
            self.account_id, self.region_name, vpc_id, cidr_block
        )

        # tags has the format: {"subnet": {"Key": ..., "Value": ...}}, but we need
        # to pass this to the generate method as {"Key": ..., "Value": ...}.  Take
        # care not to alter the original tags dict otherwise moto will not be able
        # to understand it.
        subnet_tags = None
        if tags is not None:
            subnet_tags = tags.get("subnet", tags)
        custom_id = resource_identifier.generate(tags=subnet_tags)

        if custom_id:
            # Check if custom id is unique within a given VPC
            for az_subnets in self.subnets.values():
                for subnet in az_subnets.values():
                    if subnet.vpc_id == vpc_id and subnet.id == custom_id:
                        raise InvalidSubnetDuplicateCustomIdError(custom_id)

        # Generate subnet with moto library
        result: ec2_models.subnets.Subnet = fn(self, *args, tags=tags, **kwargs)
        availability_zone = result.availability_zone

        if custom_id:
            # Remove the subnet from the default dict and add it back with the custom id
            self.subnets[availability_zone].pop(result.id)
            old_id = result.id
            result.id = custom_id
            self.subnets[availability_zone][custom_id] = result

            # Tags are not stored in the Subnet object, but instead stored in a separate
            # dict in the EC2 backend, keyed by subnet id.  That therefore requires
            # updating as well.
            if old_id in self.tags:
                self.tags[custom_id] = self.tags.pop(old_id)

        # Return the subnet with the patched custom id
        return result