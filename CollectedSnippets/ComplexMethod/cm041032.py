def create_change_set(
        self, context: RequestContext, request: CreateChangeSetInput
    ) -> CreateChangeSetOutput:
        state = get_cloudformation_store(context.account_id, context.region)

        req_params = request
        change_set_type = req_params.get("ChangeSetType", "UPDATE")
        stack_name = req_params.get("StackName")
        if not stack_name:
            raise ValidationError("Member must have length greater than or equal to 1")
        change_set_name = req_params.get("ChangeSetName")
        template_body = req_params.get("TemplateBody")
        # s3 or secretsmanager url
        template_url = req_params.get("TemplateURL")

        # validate and resolve template
        if template_body and template_url:
            raise ValidationError(
                "Specify exactly one of 'TemplateBody' or 'TemplateUrl'"
            )  # TODO: check proper message

        if not template_body and not template_url:
            raise ValidationError(
                "Specify exactly one of 'TemplateBody' or 'TemplateUrl'"
            )  # TODO: check proper message

        api_utils.prepare_template_body(
            req_params
        )  # TODO: function has too many unclear responsibilities
        if not template_body:
            template_body = req_params[
                "TemplateBody"
            ]  # should then have been set by prepare_template_body
        template = template_preparer.parse_template(req_params["TemplateBody"])

        del req_params["TemplateBody"]  # TODO: stop mutating req_params
        template["StackName"] = stack_name
        # TODO: validate with AWS what this is actually doing?
        template["ChangeSetName"] = change_set_name

        # this is intentionally not in a util yet. Let's first see how the different operations deal with these before generalizing
        # handle ARN stack_name here (not valid for initial CREATE, since stack doesn't exist yet)
        if ARN_STACK_REGEX.match(stack_name):
            if not (stack := state.stacks.get(stack_name)):
                raise ValidationError(f"Stack '{stack_name}' does not exist.")
        else:
            # stack name specified, so fetch the stack by name
            stack_candidates: list[Stack] = [
                s for stack_arn, s in state.stacks.items() if s.stack_name == stack_name
            ]
            active_stack_candidates = [
                s for s in stack_candidates if self._stack_status_is_active(s.status)
            ]

            # on a CREATE an empty Stack should be generated if we didn't find an active one
            if not active_stack_candidates and change_set_type == ChangeSetType.CREATE:
                empty_stack_template = dict(template)
                empty_stack_template["Resources"] = {}
                req_params_copy = clone_stack_params(req_params)
                stack = Stack(
                    context.account_id,
                    context.region,
                    req_params_copy,
                    empty_stack_template,
                    template_body=template_body,
                )
                state.stacks[stack.stack_id] = stack
                stack.set_stack_status("REVIEW_IN_PROGRESS")
            else:
                if not active_stack_candidates:
                    raise ValidationError(f"Stack '{stack_name}' does not exist.")
                stack = active_stack_candidates[0]

        # TODO: test if rollback status is allowed as well
        if (
            change_set_type == ChangeSetType.CREATE
            and stack.status != StackStatus.REVIEW_IN_PROGRESS
        ):
            raise ValidationError(
                f"Stack [{stack_name}] already exists and cannot be created again with the changeSet [{change_set_name}]."
            )

        old_parameters: dict[str, Parameter] = {}
        match change_set_type:
            case ChangeSetType.UPDATE:
                # add changeset to existing stack
                old_parameters = {
                    k: mask_no_echo(strip_parameter_type(v))
                    for k, v in stack.resolved_parameters.items()
                }
            case ChangeSetType.IMPORT:
                raise NotImplementedError()  # TODO: implement importing resources
            case ChangeSetType.CREATE:
                pass
            case _:
                msg = (
                    f"1 validation error detected: Value '{change_set_type}' at 'changeSetType' failed to satisfy "
                    f"constraint: Member must satisfy enum value set: [IMPORT, UPDATE, CREATE] "
                )
                raise ValidationError(msg)

        # resolve parameters
        new_parameters: dict[str, Parameter] = param_resolver.convert_stack_parameters_to_dict(
            request.get("Parameters")
        )
        parameter_declarations = param_resolver.extract_stack_parameter_declarations(template)
        resolved_parameters = param_resolver.resolve_parameters(
            account_id=context.account_id,
            region_name=context.region,
            parameter_declarations=parameter_declarations,
            new_parameters=new_parameters,
            old_parameters=old_parameters,
        )

        # TODO: remove this when fixing Stack.resources and transformation order
        #   currently we need to create a stack with existing resources + parameters so that resolve refs recursively in here will work.
        #   The correct way to do it would be at a later stage anyway just like a normal intrinsic function
        req_params_copy = clone_stack_params(req_params)
        temp_stack = Stack(context.account_id, context.region, req_params_copy, template)
        temp_stack.set_resolved_parameters(resolved_parameters)

        # TODO: everything below should be async
        # apply template transformations
        transformed_template = template_preparer.transform_template(
            context.account_id,
            context.region,
            template,
            stack_name=temp_stack.stack_name,
            resources=temp_stack.resources,
            mappings=temp_stack.mappings,
            conditions={},  # TODO: we don't have any resolved conditions yet at this point but we need the conditions because of the samtranslator...
            resolved_parameters=resolved_parameters,
        )

        # perform basic static analysis on the template
        for validation_fn in DEFAULT_TEMPLATE_VALIDATIONS:
            validation_fn(template)

        # create change set for the stack and apply changes
        change_set = StackChangeSet(
            context.account_id, context.region, stack, req_params, transformed_template
        )
        # only set parameters for the changeset, then switch to stack on execute_change_set
        change_set.set_resolved_parameters(resolved_parameters)
        change_set.template_body = template_body

        # TODO: evaluate conditions
        raw_conditions = transformed_template.get("Conditions", {})
        resolved_stack_conditions = resolve_stack_conditions(
            account_id=context.account_id,
            region_name=context.region,
            conditions=raw_conditions,
            parameters=resolved_parameters,
            mappings=temp_stack.mappings,
            stack_name=stack_name,
        )
        change_set.set_resolved_stack_conditions(resolved_stack_conditions)

        # a bit gross but use the template ordering to validate missing resources
        try:
            order_resources(
                transformed_template["Resources"],
                resolved_parameters=resolved_parameters,
                resolved_conditions=resolved_stack_conditions,
            )
        except NoResourceInStack as e:
            raise ValidationError(str(e)) from e

        deployer = template_deployer.TemplateDeployer(
            context.account_id, context.region, change_set
        )
        changes = deployer.construct_changes(
            stack,
            change_set,
            change_set_id=change_set.change_set_id,
            append_to_changeset=True,
            filter_unchanged_resources=True,
        )
        stack.change_sets.append(change_set)
        if not changes:
            change_set.metadata["Status"] = "FAILED"
            change_set.metadata["ExecutionStatus"] = "UNAVAILABLE"
            change_set.metadata["StatusReason"] = (
                "The submitted information didn't contain changes. Submit different information to create a change set."
            )
        else:
            change_set.metadata["Status"] = (
                "CREATE_COMPLETE"  # technically for some time this should first be CREATE_PENDING
            )
            change_set.metadata["ExecutionStatus"] = (
                "AVAILABLE"  # technically for some time this should first be UNAVAILABLE
            )

        return CreateChangeSetOutput(StackId=change_set.stack_id, Id=change_set.change_set_id)