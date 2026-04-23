def _get_serialized_name(self, shape: Shape, default_name: str, node: dict) -> str:
        """
        SQS allows using both - the proper serialized name of a map as well as the member name - as name for maps.
        For example, both works for the TagQueue operation:
        - Using the proper serialized name "Tag": Tag.1.Key=key&Tag.1.Value=value
        - Using the member name "Tag" in the parent structure: Tags.1.Key=key&Tags.1.Value=value
        - Using "Name" to represent the Key for a nested dict: MessageAttributes.1.Name=key&MessageAttributes.1.Value.StringValue=value
            resulting in {MessageAttributes: {key : {StringValue: value}}}
        The Java SDK implements the second variant: https://github.com/aws/aws-sdk-java-v2/issues/2524
        This has been approved to be a bug and against the spec, but since the client has a lot of users, and AWS SQS
        supports both, we need to handle it here.
        """
        # ask the super implementation for the proper serialized name
        primary_name = super()._get_serialized_name(shape, default_name, node)

        # determine potential suffixes for the name of the member in the node
        suffixes = []
        if shape.type_name == "map":
            if not shape.serialization.get("flattened"):
                suffixes = [".entry.1.Key", ".entry.1.Name"]
            else:
                suffixes = [".1.Key", ".1.Name"]
        if shape.type_name == "list":
            if not shape.serialization.get("flattened"):
                suffixes = [".member.1"]
            else:
                suffixes = [".1"]

        # if the primary name is _not_ available in the node, but the default name is, we use the default name
        if not any(f"{primary_name}{suffix}" in node for suffix in suffixes) and any(
            f"{default_name}{suffix}" in node for suffix in suffixes
        ):
            return default_name
        # otherwise we use the primary name
        return primary_name