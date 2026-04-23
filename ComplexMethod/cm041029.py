def update_stack(
        self,
        context: RequestContext,
        request: UpdateStackInput,
    ) -> UpdateStackOutput:
        stack_name = request.get("StackName")
        stack = find_stack(context.account_id, context.region, stack_name)
        if not stack:
            return not_found_error(f'Unable to update non-existing stack "{stack_name}"')

        api_utils.prepare_template_body(request)
        template = template_preparer.parse_template(request["TemplateBody"])

        if (
            "CAPABILITY_AUTO_EXPAND" not in request.get("Capabilities", [])
            and "Transform" in template.keys()
        ):
            raise InsufficientCapabilitiesException(
                "Requires capabilities : [CAPABILITY_AUTO_EXPAND]"
            )

        new_parameters: dict[str, Parameter] = param_resolver.convert_stack_parameters_to_dict(
            request.get("Parameters")
        )
        parameter_declarations = param_resolver.extract_stack_parameter_declarations(template)
        resolved_parameters = param_resolver.resolve_parameters(
            account_id=context.account_id,
            region_name=context.region,
            parameter_declarations=parameter_declarations,
            new_parameters=new_parameters,
            old_parameters=stack.resolved_parameters,
        )

        resolved_stack_conditions = resolve_stack_conditions(
            account_id=context.account_id,
            region_name=context.region,
            conditions=template.get("Conditions", {}),
            parameters=resolved_parameters,
            mappings=template.get("Mappings", {}),
            stack_name=stack_name,
        )

        raw_new_template = copy.deepcopy(template)
        try:
            template = template_preparer.transform_template(
                context.account_id,
                context.region,
                template,
                stack.stack_name,
                stack.resources,
                stack.mappings,
                resolved_stack_conditions,
                resolved_parameters,
            )
            processed_template = copy.deepcopy(
                template
            )  # copying it here since it's being mutated somewhere downstream
        except FailedTransformationException as e:
            stack.add_stack_event(
                stack.stack_name,
                stack.stack_id,
                status="ROLLBACK_IN_PROGRESS",
                status_reason=e.message,
            )
            stack.set_stack_status("ROLLBACK_COMPLETE")
            return CreateStackOutput(StackId=stack.stack_id)

        # perform basic static analysis on the template
        for validation_fn in DEFAULT_TEMPLATE_VALIDATIONS:
            validation_fn(template)

        # update the template
        stack.template_original = template

        deployer = template_deployer.TemplateDeployer(context.account_id, context.region, stack)
        # TODO: there shouldn't be a "new" stack on update
        new_stack = Stack(
            context.account_id, context.region, request, template, request["TemplateBody"]
        )
        new_stack.set_resolved_parameters(resolved_parameters)
        stack.set_resolved_parameters(resolved_parameters)
        stack.set_resolved_stack_conditions(resolved_stack_conditions)
        try:
            deployer.update_stack(new_stack)
        except NoStackUpdates as e:
            stack.set_stack_status("UPDATE_COMPLETE")
            if raw_new_template != processed_template:
                # processed templates seem to never return an exception here
                return UpdateStackOutput(StackId=stack.stack_id)
            raise ValidationError(str(e))
        except Exception as e:
            stack.set_stack_status("UPDATE_FAILED")
            msg = f'Unable to update stack "{stack_name}": {e}'
            LOG.error("%s", msg, exc_info=LOG.isEnabledFor(logging.DEBUG))
            raise ValidationError(msg) from e

        return UpdateStackOutput(StackId=stack.stack_id)