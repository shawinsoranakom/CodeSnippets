def visit_node_resource(
        self, node_resource: NodeResource
    ) -> PreprocEntityDelta[PreprocResource, PreprocResource]:
        """
        Overrides the default preprocessing for NodeResource objects by annotating the
        `after` delta with the physical resource ID, if side effects resulted in an update.
        """
        try:
            delta = super().visit_node_resource(node_resource=node_resource)
        except Exception as e:
            LOG.debug(
                "preprocessing resource '%s' failed: %s",
                node_resource.name,
                e,
                exc_info=LOG.isEnabledFor(logging.DEBUG) and config.CFN_VERBOSE_ERRORS,
            )
            self._process_event(
                action=node_resource.change_type.to_change_action(),
                logical_resource_id=node_resource.name,
                event_status=OperationStatus.FAILED,
                resource_type=node_resource.type_.value,
                reason=str(e),
            )
            raise e

        before = delta.before
        after = delta.after

        if before != after:
            # There are changes for this resource.
            self._execute_resource_change(name=node_resource.name, before=before, after=after)
        else:
            # There are no updates for this resource; iff the resource was previously
            # deployed, then the resolved details are copied in the current state for
            # references or other downstream operations.
            if not is_nothing(before):
                before_logical_id = delta.before.logical_id
                before_resource = self._before_resolved_resources.get(before_logical_id, {})
                self.resources[before_logical_id] = before_resource

        # Update the latest version of this resource for downstream references.
        if not is_nothing(after):
            after_logical_id = after.logical_id
            resource = self.resources[after_logical_id]
            resource_failed_to_deploy = resource["ResourceStatus"] in {
                ResourceStatus.CREATE_FAILED,
                ResourceStatus.UPDATE_FAILED,
            }
            if not resource_failed_to_deploy:
                after_physical_id: str = self._after_resource_physical_id(
                    resource_logical_id=after_logical_id
                )
                after.physical_resource_id = after_physical_id
            after.status = resource["ResourceStatus"]

            # terminate the deployment process
            if resource_failed_to_deploy:
                raise TriggerRollback(
                    logical_resource_id=after_logical_id,
                    reason=resource.get("ResourceStatusReason"),
                )
        return delta