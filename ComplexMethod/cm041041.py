def create_change_set(
        self, context: RequestContext, request: CreateChangeSetInput
    ) -> CreateChangeSetOutput:
        stack_name = request.get("StackName")
        if not stack_name:
            # TODO: proper exception
            raise ValidationError("StackName must be specified")
        try:
            change_set_name = request["ChangeSetName"]
        except KeyError:
            # TODO: proper exception
            raise ValidationError("StackName must be specified")

        state = get_cloudformation_store(context.account_id, context.region)

        change_set_type = request.get("ChangeSetType", "UPDATE")
        template_body = request.get("TemplateBody")
        # s3 or secretsmanager url
        template_url = request.get("TemplateURL")

        # validate and resolve template
        if template_body and template_url:
            raise ValidationError(
                "Specify exactly one of 'TemplateBody' or 'TemplateUrl'"
            )  # TODO: check proper message

        if not template_body and not template_url:
            raise ValidationError(
                "Specify exactly one of 'TemplateBody' or 'TemplateUrl'"
            )  # TODO: check proper message

        template_body = api_utils.extract_template_body(request)
        structured_template = template_preparer.parse_template(template_body)

        if len(template_body) > 51200 and not template_url:
            raise ValidationError(
                f"1 validation error detected: Value '{template_body}' at 'templateBody' "
                "failed to satisfy constraint: Member must have length less than or equal to 51200"
            )

        # this is intentionally not in a util yet. Let's first see how the different operations deal with these before generalizing
        # handle ARN stack_name here (not valid for initial CREATE, since stack doesn't exist yet)
        if is_stack_arn(stack_name):
            stack = state.stacks_v2.get(stack_name)
            if not stack:
                raise ValidationError(f"Stack '{stack_name}' does not exist.")
            stack.capabilities = request.get("Capabilities") or []
        else:
            # stack name specified, so fetch the stack by name
            stack_candidates: list[Stack] = [
                s for stack_arn, s in state.stacks_v2.items() if s.stack_name == stack_name
            ]
            active_stack_candidates = [s for s in stack_candidates if s.is_active()]

            # on a CREATE an empty Stack should be generated if we didn't find an active one
            if not active_stack_candidates and change_set_type == ChangeSetType.CREATE:
                stack = Stack(
                    account_id=context.account_id,
                    region_name=context.region,
                    request_payload=request,
                    initial_status=StackStatus.REVIEW_IN_PROGRESS,
                )
                state.stacks_v2[stack.stack_id] = stack
            else:
                if not active_stack_candidates:
                    raise ValidationError(f"Stack '{stack_name}' does not exist.")
                stack = active_stack_candidates[0]
                # propagate capabilities from create change set request
                stack.capabilities = request.get("Capabilities") or []

        # TODO: test if rollback status is allowed as well
        if (
            change_set_type == ChangeSetType.CREATE
            and stack.status != StackStatus.REVIEW_IN_PROGRESS
        ):
            raise ValidationError(
                f"Stack [{stack_name}] already exists and cannot be created again with the changeSet [{change_set_name}]."
            )

        if change_set_type == ChangeSetType.UPDATE and (
            stack.status == StackStatus.DELETE_COMPLETE
            or stack.status == StackStatus.DELETE_IN_PROGRESS
        ):
            raise ValidationError(
                f"Stack:{stack.stack_id} is in {stack.status} state and can not be updated."
            )

        before_parameters: dict[str, Parameter] | None = None
        match change_set_type:
            case ChangeSetType.UPDATE:
                before_parameters = stack.resolved_parameters
                # add changeset to existing stack
                # old_parameters = {
                #     k: mask_no_echo(strip_parameter_type(v))
                #     for k, v in stack.resolved_parameters.items()
                # }
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

        # TODO: reconsider the way parameters are modelled in the update graph process.
        #  The options might be reduce to using the current style, or passing the extra information
        #  as a metadata object. The choice should be made considering when the extra information
        #  is needed for the update graph building, or only looked up in downstream tasks (metadata).
        request_parameters = request.get("Parameters", [])
        # TODO: handle parameter defaults and resolution
        after_parameters = self._extract_after_parameters(request_parameters, before_parameters)

        # TODO: update this logic to always pass the clean template object if one exists. The
        #  current issue with relaying on stack.template_original is that this appears to have
        #  its parameters and conditions populated.
        before_template = None
        if change_set_type == ChangeSetType.UPDATE:
            before_template = stack.template
        after_template = structured_template

        previous_update_model = None
        try:
            # FIXME: 'change_set_id' for 'stack' objects is dynamically attributed
            if previous_change_set := find_change_set_v2(state, stack.change_set_id):
                previous_update_model = previous_change_set.update_model
        except Exception:
            # No change set available on this stack.
            pass

        # create change set for the stack and apply changes
        change_set = ChangeSet(
            stack,
            request,
            template=after_template,
            template_body=template_body,
        )
        self._setup_change_set_model(
            change_set=change_set,
            before_template=before_template,
            after_template=after_template,
            before_parameters=before_parameters,
            after_parameters=after_parameters,
            previous_update_model=previous_update_model,
        )
        if change_set.status == ChangeSetStatus.FAILED:
            change_set.set_execution_status(ExecutionStatus.UNAVAILABLE)
        else:
            if not change_set.has_changes():
                change_set.set_change_set_status(ChangeSetStatus.FAILED)
                change_set.set_execution_status(ExecutionStatus.UNAVAILABLE)
                change_set.status_reason = "The submitted information didn't contain changes. Submit different information to create a change set."
            else:
                if stack.status not in [StackStatus.CREATE_COMPLETE, StackStatus.UPDATE_COMPLETE]:
                    stack.set_stack_status(StackStatus.REVIEW_IN_PROGRESS, "User Initiated")

                change_set.set_change_set_status(ChangeSetStatus.CREATE_COMPLETE)

        stack.change_set_ids.add(change_set.change_set_id)
        state.change_sets[change_set.change_set_id] = change_set
        return CreateChangeSetOutput(StackId=stack.stack_id, Id=change_set.change_set_id)