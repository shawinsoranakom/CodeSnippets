def create_stack(self, context: RequestContext, request: CreateStackInput) -> CreateStackOutput:
        # TODO: test what happens when both TemplateUrl and Body are specified
        state = get_cloudformation_store(context.account_id, context.region)

        stack_name = request.get("StackName")

        # get stacks by name
        active_stack_candidates = [
            s
            for s in state.stacks.values()
            if s.stack_name == stack_name and self._stack_status_is_active(s.status)
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

        template_body = request.get("TemplateBody") or ""
        if len(template_body) > 51200:
            raise ValidationError(
                f"1 validation error detected: Value '{request['TemplateBody']}' at 'templateBody' "
                "failed to satisfy constraint: Member must have length less than or equal to 51200"
            )
        api_utils.prepare_template_body(request)  # TODO: avoid mutating request directly

        template = template_preparer.parse_template(request["TemplateBody"])

        stack_name = template["StackName"] = request.get("StackName")
        if api_utils.validate_stack_name(stack_name) is False:
            raise ValidationError(
                f"1 validation error detected: Value '{stack_name}' at 'stackName' failed to satisfy constraint:\
                Member must satisfy regular expression pattern: [a-zA-Z][-a-zA-Z0-9]*|arn:[-a-zA-Z0-9:/._+]*"
            )

        if (
            "CAPABILITY_AUTO_EXPAND" not in request.get("Capabilities", [])
            and "Transform" in template.keys()
        ):
            raise InsufficientCapabilitiesException(
                "Requires capabilities : [CAPABILITY_AUTO_EXPAND]"
            )

        # resolve stack parameters
        new_parameters = param_resolver.convert_stack_parameters_to_dict(request.get("Parameters"))
        parameter_declarations = param_resolver.extract_stack_parameter_declarations(template)
        resolved_parameters = param_resolver.resolve_parameters(
            account_id=context.account_id,
            region_name=context.region,
            parameter_declarations=parameter_declarations,
            new_parameters=new_parameters,
            old_parameters={},
        )

        stack = Stack(context.account_id, context.region, request, template)

        try:
            template = template_preparer.transform_template(
                context.account_id,
                context.region,
                template,
                stack.stack_name,
                stack.resources,
                stack.mappings,
                {},  # TODO
                resolved_parameters,
            )
        except FailedTransformationException as e:
            stack.add_stack_event(
                stack.stack_name,
                stack.stack_id,
                status="ROLLBACK_IN_PROGRESS",
                status_reason=e.message,
            )
            stack.set_stack_status("ROLLBACK_COMPLETE")
            state.stacks[stack.stack_id] = stack
            return CreateStackOutput(StackId=stack.stack_id)

        # HACK: recreate the stack (including all of its confusing processes in the __init__ method
        # to set the stack template to be the transformed template, rather than the untransformed
        # template
        stack = Stack(context.account_id, context.region, request, template)

        # perform basic static analysis on the template
        for validation_fn in DEFAULT_TEMPLATE_VALIDATIONS:
            validation_fn(template)

        # resolve conditions
        raw_conditions = template.get("Conditions", {})
        resolved_stack_conditions = resolve_stack_conditions(
            account_id=context.account_id,
            region_name=context.region,
            conditions=raw_conditions,
            parameters=resolved_parameters,
            mappings=stack.mappings,
            stack_name=stack_name,
        )
        stack.set_resolved_stack_conditions(resolved_stack_conditions)

        stack.set_resolved_parameters(resolved_parameters)
        stack.template_body = template_body
        state.stacks[stack.stack_id] = stack
        LOG.debug(
            'Creating stack "%s" with %s resources ...',
            stack.stack_name,
            len(stack.template_resources),
        )
        deployer = template_deployer.TemplateDeployer(context.account_id, context.region, stack)
        try:
            deployer.deploy_stack()
        except Exception as e:
            stack.set_stack_status("CREATE_FAILED")
            msg = f'Unable to create stack "{stack.stack_name}": {e}'
            LOG.error("%s", exc_info=LOG.isEnabledFor(logging.DEBUG))
            raise ValidationError(msg) from e

        return CreateStackOutput(StackId=stack.stack_id)