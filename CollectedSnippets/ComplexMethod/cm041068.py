def apply_change(self, change: ChangeConfig, stack: Stack) -> None:
        change_details = change["ResourceChange"]
        action = change_details["Action"]
        resource_id = change_details["LogicalResourceId"]
        resources = stack.resources
        resource = resources[resource_id]

        # TODO: this should not be needed as resources are filtered out if the
        # condition evaluates to False.
        if not evaluate_resource_condition(stack.resolved_conditions, resource):
            return

        # remove AWS::NoValue entries
        resource_props = resource.get("Properties")
        if resource_props:
            resource["Properties"] = remove_none_values(resource_props)

        executor = self.create_resource_provider_executor()
        resource_provider_payload = self.create_resource_provider_payload(
            action, logical_resource_id=resource_id
        )

        resource_type = get_resource_type(resource)
        resource_provider = executor.try_load_resource_provider(resource_type)
        track_resource_operation(action, resource_type, missing=resource_provider is None)
        if resource_provider is not None:
            # add in-progress event
            resource_status = f"{get_action_name_for_resource_change(action)}_IN_PROGRESS"
            physical_resource_id = None
            if action in ("Modify", "Remove"):
                previous_state = self.resources[resource_id].get("_last_deployed_state")
                if not previous_state:
                    # TODO: can this happen?
                    previous_state = self.resources[resource_id]["Properties"]
                physical_resource_id = executor.extract_physical_resource_id_from_model_with_schema(
                    resource_model=previous_state,
                    resource_type=resource["Type"],
                    resource_type_schema=resource_provider.SCHEMA,
                )
            stack.add_stack_event(
                resource_id=resource_id,
                physical_res_id=physical_resource_id,
                status=resource_status,
            )

            # perform the deploy
            progress_event = executor.deploy_loop(
                resource_provider, resource, resource_provider_payload
            )
        else:
            # track that we don't handle the resource, and possibly raise an exception
            log_not_available_message(
                resource_type,
                f'No resource provider found for "{resource_type}"',
            )

            if not config.CFN_IGNORE_UNSUPPORTED_RESOURCE_TYPES:
                raise NoResourceProvider

            resource["PhysicalResourceId"] = MOCK_REFERENCE
            progress_event = ProgressEvent(OperationStatus.SUCCESS, resource_model={})

        # TODO: clean up the surrounding loop (do_apply_changes_in_loop) so that the responsibilities are clearer
        stack_action = get_action_name_for_resource_change(action)
        match progress_event.status:
            case OperationStatus.FAILED:
                stack.set_resource_status(
                    resource_id,
                    f"{stack_action}_FAILED",
                    status_reason=progress_event.message or "",
                )
                # TODO: remove exception raising here?
                # TODO: fix request token
                raise Exception(
                    f'Resource handler returned message: "{progress_event.message}" (RequestToken: 10c10335-276a-33d3-5c07-018b684c3d26, HandlerErrorCode: InvalidRequest){progress_event.error_code}'
                )
            case OperationStatus.SUCCESS:
                stack.set_resource_status(resource_id, f"{stack_action}_COMPLETE")
            case OperationStatus.PENDING:
                # signal to the main loop that we should come back to this resource in the future
                raise DependencyNotYetSatisfied(
                    resource_ids=[], message="Resource dependencies not yet satisfied"
                )
            case OperationStatus.IN_PROGRESS:
                raise Exception("Resource deployment loop should not finish in this state")
            case unknown_status:
                raise Exception(f"Unknown operation status: {unknown_status}")

        # TODO: this is probably already done in executor, try removing this
        resource["Properties"] = progress_event.resource_model