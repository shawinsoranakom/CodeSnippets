def add_permission(
        self,
        context: RequestContext,
        request: AddPermissionRequest,
    ) -> AddPermissionResponse:
        function_name, qualifier = api_utils.get_name_and_qualifier(
            request.get("FunctionName"), request.get("Qualifier"), context
        )

        # validate qualifier
        if qualifier is not None:
            self._validate_qualifier_expression(qualifier)
            if qualifier == "$LATEST":
                raise InvalidParameterValueException(
                    "We currently do not support adding policies for $LATEST.", Type="User"
                )
        account_id, region = api_utils.get_account_and_region(request.get("FunctionName"), context)

        resolved_fn = self._get_function(function_name, account_id, region)
        resolved_qualifier, fn_arn = self._resolve_fn_qualifier(resolved_fn, qualifier)

        revision_id = request.get("RevisionId")
        if revision_id:
            fn_revision_id = self._function_revision_id(resolved_fn, resolved_qualifier)
            if revision_id != fn_revision_id:
                raise PreconditionFailedException(
                    "The Revision Id provided does not match the latest Revision Id. "
                    "Call the GetPolicy API to retrieve the latest Revision Id",
                    Type="User",
                )

        request_sid = request["StatementId"]
        if not bool(STATEMENT_ID_REGEX.match(request_sid)):
            raise ValidationException(
                f"1 validation error detected: Value '{request_sid}' at 'statementId' failed to satisfy constraint: Member must satisfy regular expression pattern: ([a-zA-Z0-9-_]+)"
            )
        # check for an already existing policy and any conflicts in existing statements
        existing_policy = resolved_fn.permissions.get(resolved_qualifier)
        if existing_policy:
            if request_sid in [s["Sid"] for s in existing_policy.policy.Statement]:
                # uniqueness scope: statement id needs to be unique per qualified function ($LATEST, version, or alias)
                # Counterexample: the same sid can exist within $LATEST, version, and alias
                raise ResourceConflictException(
                    f"The statement id ({request_sid}) provided already exists. Please provide a new statement id, or remove the existing statement.",
                    Type="User",
                )

        permission_statement = api_utils.build_statement(
            partition=context.partition,
            resource_arn=fn_arn,
            statement_id=request["StatementId"],
            action=request["Action"],
            principal=request["Principal"],
            source_arn=request.get("SourceArn"),
            source_account=request.get("SourceAccount"),
            principal_org_id=request.get("PrincipalOrgID"),
            event_source_token=request.get("EventSourceToken"),
            auth_type=request.get("FunctionUrlAuthType"),
        )
        new_policy = existing_policy
        if not existing_policy:
            new_policy = FunctionResourcePolicy(
                policy=ResourcePolicy(Version="2012-10-17", Id="default", Statement=[])
            )
        new_policy.policy.Statement.append(permission_statement)
        if not existing_policy:
            resolved_fn.permissions[resolved_qualifier] = new_policy

        # Update revision id of alias or version
        # TODO: re-evaluate data model to prevent this dirty hack just for bumping the revision id
        # TODO: does that need a `with function.lock` for atomic updates of the policy + revision_id?
        if api_utils.qualifier_is_alias(resolved_qualifier):
            resolved_alias = resolved_fn.aliases[resolved_qualifier]
            resolved_fn.aliases[resolved_qualifier] = dataclasses.replace(resolved_alias)
        # Assumes that a non-alias is a version
        else:
            resolved_version = resolved_fn.versions[resolved_qualifier]
            resolved_fn.versions[resolved_qualifier] = dataclasses.replace(
                resolved_version, config=dataclasses.replace(resolved_version.config)
            )
        return AddPermissionResponse(Statement=json.dumps(permission_statement))