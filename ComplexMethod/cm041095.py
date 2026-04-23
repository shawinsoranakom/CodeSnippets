def _execute_resource_action(
        self,
        action: ChangeAction,
        logical_resource_id: str,
        resource_type: str,
        before_properties: PreprocProperties | None,
        after_properties: PreprocProperties | None,
        part_of_replacement: bool = False,
    ) -> ProgressEvent:
        LOG.debug("Executing resource action: %s for resource '%s'", action, logical_resource_id)
        payload = self.create_resource_provider_payload(
            action=action,
            logical_resource_id=logical_resource_id,
            resource_type=resource_type,
            before_properties=before_properties,
            after_properties=after_properties,
        )
        resource_provider = self.resource_provider_executor.try_load_resource_provider(
            resource_type
        )
        track_resource_operation(action, resource_type, missing=resource_provider is not None)

        extra_resource_properties = {}
        if resource_provider is not None:
            try:
                event = self.resource_provider_executor.deploy_loop(
                    resource_provider, extra_resource_properties, payload
                )
            except Exception as e:
                reason = str(e)
                LOG.warning(
                    "Resource provider operation failed: '%s'",
                    reason,
                    exc_info=LOG.isEnabledFor(logging.DEBUG) and config.CFN_VERBOSE_ERRORS,
                )
                event = ProgressEvent(
                    OperationStatus.FAILED,
                    resource_model={},
                    message=f"Resource provider operation failed: {reason}",
                    custom_context={"exception": e},
                )
        elif should_ignore_unsupported_resource_type(
            resource_type=resource_type, change_set_type=self._change_set.change_set_type
        ):
            log_not_available_message(
                resource_type,
                f'No resource provider found for "{resource_type}"',
            )
            if "CFN_IGNORE_UNSUPPORTED_RESOURCE_TYPES" not in os.environ:
                LOG.warning(
                    "Deployment of resource type %s succeeded, but will fail in upcoming LocalStack releases unless CFN_IGNORE_UNSUPPORTED_RESOURCE_TYPES is explicitly enabled.",
                    resource_type,
                )
            event = ProgressEvent(
                OperationStatus.SUCCESS,
                resource_model={},
                message=f"Resource type {resource_type} is not supported but was deployed as a fallback",
            )
        else:
            log_not_available_message(
                resource_type,
                f'No resource provider found for "{resource_type}"',
            )
            event = ProgressEvent(
                OperationStatus.FAILED,
                resource_model={},
                message=f"Resource type {resource_type} not supported",
            )

        if part_of_replacement and action == ChangeAction.Remove:
            # Early return as we don't want to update internal state of the executor if this is a
            # cleanup of an old resource. The new resource has already been created and the state
            # updated
            return event

        status_from_action = EventOperationFromAction[action.value]
        resolved_resource = ResolvedResource(
            Properties=event.resource_model,
            LogicalResourceId=logical_resource_id,
            Type=resource_type,
            LastUpdatedTimestamp=datetime.now(UTC),
        )
        match event.status:
            case OperationStatus.SUCCESS:
                # merge the resources state with the external state
                # TODO: this is likely a duplicate of updating from extra_resource_properties

                # TODO: add typing
                # TODO: avoid the use of string literals for sampling from the object, use typed classes instead
                # TODO: avoid sampling from resources and use tmp var reference
                # TODO: add utils functions to abstract this logic away (resource.update(..))
                # TODO: avoid the use of setdefault (debuggability/readability)
                # TODO: review the use of merge

                # Don't update the resolved resources if we have deleted that resource
                if action != ChangeAction.Remove:
                    physical_resource_id = (
                        extra_resource_properties["PhysicalResourceId"]
                        if resource_provider
                        else MOCKED_REFERENCE
                    )
                    resolved_resource["PhysicalResourceId"] = physical_resource_id
                    resolved_resource["ResourceStatus"] = ResourceStatus(
                        f"{status_from_action}_COMPLETE"
                    )
                    # TODO: do we actually need this line?
                    resolved_resource.update(extra_resource_properties)
            case OperationStatus.FAILED:
                reason = event.message
                LOG.warning(
                    "Resource provider operation failed: '%s'",
                    reason,
                )
                resolved_resource["ResourceStatus"] = ResourceStatus(f"{status_from_action}_FAILED")
                resolved_resource["ResourceStatusReason"] = reason

                exception = event.custom_context.get("exception")
                emit_stack_failure(reason, exception=exception)

            case other:
                raise NotImplementedError(f"Event status '{other}' not handled")

        self.resources[logical_resource_id] = resolved_resource
        return event