def add_layer_version_permission(
        self,
        context: RequestContext,
        layer_name: LayerName,
        version_number: LayerVersionNumber,
        statement_id: StatementId,
        action: LayerPermissionAllowedAction,
        principal: LayerPermissionAllowedPrincipal,
        organization_id: OrganizationId = None,
        revision_id: String = None,
        **kwargs,
    ) -> AddLayerVersionPermissionResponse:
        # `layer_name` can either be layer name or ARN. It is used to generate error messages.
        # `layer_n` contains the layer name.
        region_name, account_id, layer_n, _ = LambdaProvider._resolve_layer(layer_name, context)

        if action != "lambda:GetLayerVersion":
            raise ValidationException(
                f"1 validation error detected: Value '{action}' at 'action' failed to satisfy constraint: Member must satisfy regular expression pattern: lambda:GetLayerVersion"
            )

        store = lambda_stores[account_id][region_name]
        layer = store.layers.get(layer_n)

        layer_version_arn = api_utils.layer_version_arn(
            layer_name, account_id, region_name, str(version_number)
        )

        if layer is None:
            raise ResourceNotFoundException(
                f"Layer version {layer_version_arn} does not exist.", Type="User"
            )
        layer_version = layer.layer_versions.get(str(version_number))
        if layer_version is None:
            raise ResourceNotFoundException(
                f"Layer version {layer_version_arn} does not exist.", Type="User"
            )
        # do we have a policy? if not set one
        if layer_version.policy is None:
            layer_version.policy = LayerPolicy()

        if statement_id in layer_version.policy.statements:
            raise ResourceConflictException(
                f"The statement id ({statement_id}) provided already exists. Please provide a new statement id, or remove the existing statement.",
                Type="User",
            )

        if revision_id and layer_version.policy.revision_id != revision_id:
            raise PreconditionFailedException(
                "The Revision Id provided does not match the latest Revision Id. "
                "Call the GetLayerPolicy API to retrieve the latest Revision Id",
                Type="User",
            )

        statement = LayerPolicyStatement(
            sid=statement_id, action=action, principal=principal, organization_id=organization_id
        )

        old_statements = layer_version.policy.statements
        layer_version.policy = dataclasses.replace(
            layer_version.policy, statements={**old_statements, statement_id: statement}
        )

        return AddLayerVersionPermissionResponse(
            Statement=json.dumps(
                {
                    "Sid": statement.sid,
                    "Effect": "Allow",
                    "Principal": statement.principal,
                    "Action": statement.action,
                    "Resource": layer_version.layer_version_arn,
                }
            ),
            RevisionId=layer_version.policy.revision_id,
        )