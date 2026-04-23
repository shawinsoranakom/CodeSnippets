def _get_account_id_and_region_for_taggable_resource(
        self, resource: TaggableResource
    ) -> tuple[str, str]:
        """
        Takes a resource ARN for a TaggableResource (Lambda Function, Event Source Mapping, Code Signing Config, or Capacity Provider) and returns a corresponding
        LambdaStore for its region and account.

        In addition, this function validates that the ARN is a valid TaggableResource type, and that the TaggableResource exists.

        Raises:
            ValidationException: If the resource ARN is not a full ARN for a TaggableResource.
            ResourceNotFoundException: If the specified resource does not exist.
            InvalidParameterValueException: If the resource ARN is a qualified Lambda Function.
        """

        def _raise_validation_exception():
            raise ValidationException(
                f"1 validation error detected: Value '{resource}' at 'resource' failed to satisfy constraint: Member must satisfy regular expression pattern: {api_utils.TAGGABLE_RESOURCE_ARN_PATTERN}"
            )

        # Check whether the ARN we have been passed is correctly formatted
        parsed_resource_arn: ArnData = None
        try:
            parsed_resource_arn = parse_arn(resource)
        except Exception:
            _raise_validation_exception()

        # TODO: Should we be checking whether this is a full ARN?
        region, account_id, resource_type = map(
            parsed_resource_arn.get, ("region", "account", "resource")
        )

        if not all((region, account_id, resource_type)):
            _raise_validation_exception()

        if not (parts := resource_type.split(":")):
            _raise_validation_exception()

        resource_type, resource_identifier, *qualifier = parts

        # Qualifier validation raises before checking for NotFound
        if qualifier:
            if resource_type == "function":
                raise InvalidParameterValueException(
                    "Tags on function aliases and versions are not supported. Please specify a function ARN.",
                    Type="User",
                )
            _raise_validation_exception()

        if resource_type == "event-source-mapping":
            self._get_esm(resource_identifier, account_id, region)
        elif resource_type == "code-signing-config":
            raise NotImplementedError("Resource tagging on CSC not yet implemented.")
        elif resource_type == "function":
            self._get_function(
                function_name=resource_identifier, account_id=account_id, region=region
            )
        elif resource_type == "capacity-provider":
            self._get_capacity_provider(resource_identifier, account_id, region)
        else:
            _raise_validation_exception()

        # If no exceptions are raised, assume ARN and referenced resource is valid for tag operations
        return account_id, region