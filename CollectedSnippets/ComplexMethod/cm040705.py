def _validate_layers(self, new_layers: list[str], region: str, account_id: str):
        if len(new_layers) > LAMBDA_LAYERS_LIMIT_PER_FUNCTION:
            raise InvalidParameterValueException(
                "Cannot reference more than 5 layers.", Type="User"
            )

        visited_layers = {}
        for layer_version_arn in new_layers:
            (
                layer_region,
                layer_account_id,
                layer_name,
                layer_version_str,
            ) = api_utils.parse_layer_arn(layer_version_arn)
            if layer_version_str is None:
                raise ValidationException(
                    f"1 validation error detected: Value '[{layer_version_arn}]'"
                    + " at 'layers' failed to satisfy constraint: Member must satisfy constraint: [Member must have length less than or equal to 2048, Member must have length greater than or equal to 1, Member must satisfy regular expression pattern: "
                    + "(arn:(aws[a-zA-Z-]*)?:lambda:(eusc-)?[a-z]{2}((-gov)|(-iso([a-z]?)))?-[a-z]+-\\d{1}:\\d{12}:layer:[a-zA-Z0-9-_]+:[0-9]+)|(arn:[a-zA-Z0-9-]+:lambda:::awslayer:[a-zA-Z0-9-_]+), Member must not be null]",
                )

            state = lambda_stores[layer_account_id][layer_region]
            layer = state.layers.get(layer_name)
            layer_version = None
            if layer is not None:
                layer_version = layer.layer_versions.get(layer_version_str)
            if layer_account_id == account_id:
                if region and layer_region != region:
                    raise InvalidParameterValueException(
                        f"Layers are not in the same region as the function. "
                        f"Layers are expected to be in region {region}.",
                        Type="User",
                    )
                if layer is None or layer.layer_versions.get(layer_version_str) is None:
                    raise InvalidParameterValueException(
                        f"Layer version {layer_version_arn} does not exist.", Type="User"
                    )
            else:  # External layer from other account
                # TODO: validate IAM layer policy here, allowing access by default for now and only checking region
                if region and layer_region != region:
                    # TODO: detect user or role from context when IAM users are implemented
                    user = "user/localstack-testing"
                    raise AccessDeniedException(
                        f"User: arn:{get_partition(region)}:iam::{account_id}:{user} is not authorized to perform: lambda:GetLayerVersion on resource: {layer_version_arn} because no resource-based policy allows the lambda:GetLayerVersion action"
                    )
                if layer is None or layer_version is None:
                    # Limitation: cannot fetch external layers when using the same account id as the target layer
                    # because we do not want to trigger the layer fetcher for every non-existing layer.
                    if self.layer_fetcher is None:
                        raise NotImplementedError(
                            "Fetching shared layers from AWS is a pro feature."
                        )

                    layer = self.layer_fetcher.fetch_layer(layer_version_arn)
                    if layer is None:
                        # TODO: detect user or role from context when IAM users are implemented
                        user = "user/localstack-testing"
                        raise AccessDeniedException(
                            f"User: arn:{get_partition(region)}:iam::{account_id}:{user} is not authorized to perform: lambda:GetLayerVersion on resource: {layer_version_arn} because no resource-based policy allows the lambda:GetLayerVersion action"
                        )

                    # Distinguish between new layer and new layer version
                    if layer_version is None:
                        # Create whole layer from scratch
                        state.layers[layer_name] = layer
                    else:
                        # Create layer version if another version of the same layer already exists
                        state.layers[layer_name].layer_versions[layer_version_str] = (
                            layer.layer_versions.get(layer_version_str)
                        )

            # only the first two matches in the array are considered for the error message
            layer_arn = ":".join(layer_version_arn.split(":")[:-1])
            if layer_arn in visited_layers:
                conflict_layer_version_arn = visited_layers[layer_arn]
                raise InvalidParameterValueException(
                    f"Two different versions of the same layer are not allowed to be referenced in the same function. {conflict_layer_version_arn} and {layer_version_arn} are versions of the same layer.",
                    Type="User",
                )
            visited_layers[layer_arn] = layer_version_arn