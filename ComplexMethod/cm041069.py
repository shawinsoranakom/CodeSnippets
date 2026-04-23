def delete_stack(self):
        if not self.stack:
            return
        self.stack.set_stack_status("DELETE_IN_PROGRESS")
        stack_resources = list(self.stack.resources.values())
        resources = {r["LogicalResourceId"]: clone_safe(r) for r in stack_resources}
        original_resources = self.stack.template_original["Resources"]

        # TODO: what is this doing?
        for key, resource in resources.items():
            resource["Properties"] = resource.get(
                "Properties", clone_safe(resource)
            )  # TODO: why is there a fallback?
            resource["ResourceType"] = get_resource_type(resource)

        ordered_resource_ids = list(
            order_resources(
                resources=original_resources,
                resolved_conditions=self.stack.resolved_conditions,
                resolved_parameters=self.stack.resolved_parameters,
                reverse=True,
            ).keys()
        )
        for i, resource_id in enumerate(ordered_resource_ids):
            resource = resources[resource_id]
            resource_type = get_resource_type(resource)
            try:
                # TODO: cache condition value in resource details on deployment and use cached value here
                if not evaluate_resource_condition(
                    self.stack.resolved_conditions,
                    resource,
                ):
                    continue

                action = "Remove"
                executor = self.create_resource_provider_executor()
                resource_provider_payload = self.create_resource_provider_payload(
                    action, logical_resource_id=resource_id
                )
                LOG.debug(
                    'Handling "Remove" for resource "%s" (%s/%s) type "%s"',
                    resource_id,
                    i + 1,
                    len(resources),
                    resource_type,
                )
                resource_provider = executor.try_load_resource_provider(resource_type)
                track_resource_operation(action, resource_type, missing=resource_provider is None)
                if resource_provider is not None:
                    event = executor.deploy_loop(
                        resource_provider, resource, resource_provider_payload
                    )
                else:
                    log_not_available_message(
                        resource_type,
                        f'No resource provider found for "{resource_type}"',
                    )

                    if not config.CFN_IGNORE_UNSUPPORTED_RESOURCE_TYPES:
                        raise NoResourceProvider
                    event = ProgressEvent(OperationStatus.SUCCESS, resource_model={})
                match event.status:
                    case OperationStatus.SUCCESS:
                        self.stack.set_resource_status(resource_id, "DELETE_COMPLETE")
                    case OperationStatus.PENDING:
                        # the resource is still being deleted, specifically the provider has
                        # signalled that the deployment loop should skip this resource this
                        # time and come back to it later, likely due to unmet child
                        # resources still existing because we don't delete things in the
                        # correct order yet.
                        continue
                    case OperationStatus.FAILED:
                        LOG.error(
                            "Failed to delete resource with id %s. Reason: %s",
                            resource_id,
                            event.message or "unknown",
                            exc_info=LOG.isEnabledFor(logging.DEBUG),
                        )
                    case OperationStatus.IN_PROGRESS:
                        # the resource provider executor should not return this state, so
                        # this state is a programming error
                        raise Exception(
                            "Programming error: ResourceProviderExecutor cannot return IN_PROGRESS"
                        )
                    case other_status:
                        raise Exception(f"Use of unsupported status found: {other_status}")

            except Exception as e:
                LOG.error(
                    "Failed to delete resource with id %s. Final exception: %s",
                    resource_id,
                    e,
                    exc_info=LOG.isEnabledFor(logging.DEBUG),
                )

        # update status
        self.stack.set_stack_status("DELETE_COMPLETE")
        self.stack.set_time_attribute("DeletionTime")