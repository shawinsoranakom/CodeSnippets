def create_stack(self, context: RequestContext, request: CreateStackInput) -> CreateStackOutput:
        try:
            stack_name = request["StackName"]
        except KeyError:
            # TODO: proper exception
            raise ValidationError("StackName must be specified")

        state = get_cloudformation_store(context.account_id, context.region)

        active_stack_candidates = [
            stack
            for stack in state.stacks_v2.values()
            if stack.stack_name == stack_name and stack.status not in [StackStatus.DELETE_COMPLETE]
        ]

        # TODO: fix/implement this code path
        #   this needs more investigation how Cloudformation handles it (e.g. normal stack create or does it create a separate changeset?)
        # REVIEW_IN_PROGRESS is another special status
        # in this case existing changesets are set to obsolete and the stack is created
        # review_stack_candidates = [s for s in stack_candidates if s.status == StackStatus.REVIEW_IN_PROGRESS]
        # if review_stack_candidates:
        # set changesets to obsolete
        # for cs in review_stack_candidates[0].change_sets:
        #     cs.execution_status = ExecutionStatus.OBSOLETE

        if active_stack_candidates:
            raise AlreadyExistsException(f"Stack [{stack_name}] already exists")

        # TODO: copied from create_change_set, consider unifying
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

        if "CAPABILITY_AUTO_EXPAND" not in request.get("Capabilities", []) and (
            "Transform" in structured_template.keys() or "Fn::Transform" in template_body
        ):
            raise InsufficientCapabilitiesException(
                "Requires capabilities : [CAPABILITY_AUTO_EXPAND]"
            )

        stack = Stack(
            account_id=context.account_id,
            region_name=context.region,
            request_payload=request,
            tags=request.get("Tags"),
        )
        # TODO: what is the correct initial status?
        state.stacks_v2[stack.stack_id] = stack

        # TODO: reconsider the way parameters are modelled in the update graph process.
        #  The options might be reduce to using the current style, or passing the extra information
        #  as a metadata object. The choice should be made considering when the extra information
        #  is needed for the update graph building, or only looked up in downstream tasks (metadata).
        request_parameters = request.get("Parameters", [])
        # TODO: handle parameter defaults and resolution
        after_parameters = self._extract_after_parameters(request_parameters)
        after_template = structured_template

        # Create internal change set to execute
        change_set = ChangeSet(
            stack,
            {"ChangeSetName": f"cs-{stack_name}-create", "ChangeSetType": ChangeSetType.CREATE},
            template=after_template,
            template_body=template_body,
        )
        self._setup_change_set_model(
            change_set=change_set,
            before_template=None,
            after_template=after_template,
            before_parameters=None,
            after_parameters=after_parameters,
            previous_update_model=None,
        )
        if change_set.status == ChangeSetStatus.FAILED:
            return CreateStackOutput(StackId=stack.stack_id)

        stack.processed_template = change_set.processed_template

        # deployment process
        stack.set_stack_status(StackStatus.CREATE_IN_PROGRESS)
        change_set_executor = ChangeSetModelExecutor(change_set)

        def _run(*args):
            try:
                result = change_set_executor.execute()
                stack.resolved_resources = result.resources
                stack.resolved_outputs = result.outputs
                if all(
                    resource["ResourceStatus"] == ResourceStatus.CREATE_COMPLETE
                    for resource in stack.resolved_resources.values()
                ):
                    stack.set_stack_status(StackStatus.CREATE_COMPLETE)
                else:
                    stack.set_stack_status(StackStatus.CREATE_FAILED)

                # if the deployment succeeded, update the stack's template representation to that
                # which was just deployed
                stack.template = change_set.template
                stack.template_body = change_set.template_body
                stack.processed_template = change_set.processed_template
                stack.resolved_parameters = change_set.resolved_parameters
                stack.resolved_exports = {}
                for output in result.outputs:
                    if export_name := output.get("ExportName"):
                        stack.resolved_exports[export_name] = output["OutputValue"]
            except Exception as e:
                LOG.error(
                    "Create Stack set failed: %s",
                    e,
                    exc_info=LOG.isEnabledFor(logging.WARNING) and config.CFN_VERBOSE_ERRORS,
                )
                stack.set_stack_status(StackStatus.CREATE_FAILED)

        start_worker_thread(_run)

        return CreateStackOutput(StackId=stack.stack_id)