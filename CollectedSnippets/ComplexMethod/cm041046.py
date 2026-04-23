def update_stack(
        self,
        context: RequestContext,
        request: UpdateStackInput,
    ) -> UpdateStackOutput:
        try:
            stack_name = request["StackName"]
        except KeyError:
            # TODO: proper exception
            raise ValidationError("StackName must be specified")
        state = get_cloudformation_store(context.account_id, context.region)
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

        if "CAPABILITY_AUTO_EXPAND" not in request.get("Capabilities", []) and (
            "Transform" in structured_template.keys() or "Fn::Transform" in template_body
        ):
            raise InsufficientCapabilitiesException(
                "Requires capabilities : [CAPABILITY_AUTO_EXPAND]"
            )

        # this is intentionally not in a util yet. Let's first see how the different operations deal with these before generalizing
        # handle ARN stack_name here (not valid for initial CREATE, since stack doesn't exist yet)
        stack: Stack
        if is_stack_arn(stack_name):
            stack = state.stacks_v2.get(stack_name)
            if not stack:
                raise ValidationError(f"Stack '{stack_name}' does not exist.")

        else:
            # stack name specified, so fetch the stack by name
            stack_candidates: list[Stack] = [
                s for stack_arn, s in state.stacks_v2.items() if s.stack_name == stack_name
            ]
            active_stack_candidates = [
                s for s in stack_candidates if self._stack_status_is_active(s.status)
            ]

            if not active_stack_candidates:
                raise ValidationError(f"Stack '{stack_name}' does not exist.")
            elif len(active_stack_candidates) > 1:
                raise RuntimeError("Multiple stacks matched, update matching logic")
            stack = active_stack_candidates[0]

        if (
            stack.status == StackStatus.DELETE_COMPLETE
            or stack.status == StackStatus.DELETE_IN_PROGRESS
        ):
            raise ValidationError(
                f"Stack:{stack.stack_id} is in {stack.status} state and can not be updated."
            )

        # TODO: proper status modeling
        before_parameters = stack.resolved_parameters
        # TODO: reconsider the way parameters are modelled in the update graph process.
        #  The options might be reduce to using the current style, or passing the extra information
        #  as a metadata object. The choice should be made considering when the extra information
        #  is needed for the update graph building, or only looked up in downstream tasks (metadata).
        request_parameters = request.get("Parameters", [])
        # TODO: handle parameter defaults and resolution
        after_parameters = self._extract_after_parameters(request_parameters, before_parameters)

        before_template = stack.template
        after_template = structured_template

        previous_update_model = None
        if stack.change_set_id:
            if previous_change_set := find_change_set_v2(state, stack.change_set_id):
                previous_update_model = previous_change_set.update_model

        change_set = ChangeSet(
            stack,
            {"ChangeSetName": f"cs-{stack_name}-create", "ChangeSetType": ChangeSetType.CREATE},
            template_body=template_body,
            template=after_template,
        )
        self._setup_change_set_model(
            change_set=change_set,
            before_template=before_template,
            after_template=after_template,
            before_parameters=before_parameters,
            after_parameters=after_parameters,
            previous_update_model=previous_update_model,
        )

        # TODO: some changes are only detectable at runtime; consider using
        #       the ChangeSetModelDescriber, or a new custom visitors, to
        #       pick-up on runtime changes.
        if not change_set.has_changes():
            raise ValidationError("No updates are to be performed.")

        stack.set_stack_status(StackStatus.UPDATE_IN_PROGRESS)
        change_set_executor = ChangeSetModelExecutor(change_set)

        def _run(*args):
            try:
                result = change_set_executor.execute()
                stack.set_stack_status(StackStatus.UPDATE_COMPLETE)
                stack.resolved_resources = result.resources
                stack.resolved_outputs = result.outputs
                # if the deployment succeeded, update the stack's template representation to that
                # which was just deployed
                stack.template = change_set.template
                stack.template_body = change_set.template_body
                stack.resolved_parameters = change_set.resolved_parameters
                stack.resolved_exports = {}
                for output in result.outputs:
                    if export_name := output.get("ExportName"):
                        stack.resolved_exports[export_name] = output["OutputValue"]
            except Exception as e:
                LOG.error(
                    "Update Stack failed: %s",
                    e,
                    exc_info=LOG.isEnabledFor(logging.WARNING) and config.CFN_VERBOSE_ERRORS,
                )
                stack.set_stack_status(StackStatus.UPDATE_FAILED)

        start_worker_thread(_run)

        return UpdateStackOutput(StackId=stack.stack_id)