def remove_layer_version_permission(
        self,
        context: RequestContext,
        layer_name: LayerName,
        version_number: LayerVersionNumber,
        statement_id: StatementId,
        revision_id: String = None,
        **kwargs,
    ) -> None:
        # `layer_name` can either be layer name or ARN. It is used to generate error messages.
        # `layer_n` contains the layer name.
        region_name, account_id, layer_n, layer_version = LambdaProvider._resolve_layer(
            layer_name, context
        )

        layer_version_arn = api_utils.layer_version_arn(
            layer_name, account_id, region_name, str(version_number)
        )

        state = lambda_stores[account_id][region_name]
        layer = state.layers.get(layer_n)
        if layer is None:
            raise ResourceNotFoundException(
                f"Layer version {layer_version_arn} does not exist.", Type="User"
            )
        layer_version = layer.layer_versions.get(str(version_number))
        if layer_version is None:
            raise ResourceNotFoundException(
                f"Layer version {layer_version_arn} does not exist.", Type="User"
            )

        if revision_id and layer_version.policy.revision_id != revision_id:
            raise PreconditionFailedException(
                "The Revision Id provided does not match the latest Revision Id. "
                "Call the GetLayerPolicy API to retrieve the latest Revision Id",
                Type="User",
            )

        if statement_id not in layer_version.policy.statements:
            raise ResourceNotFoundException(
                f"Statement {statement_id} is not found in resource policy.", Type="User"
            )

        old_statements = layer_version.policy.statements
        layer_version.policy = dataclasses.replace(
            layer_version.policy,
            statements={k: v for k, v in old_statements.items() if k != statement_id},
        )