def visit_node_resource(
        self, node_resource: NodeResource
    ) -> PreprocEntityDelta[PreprocResource, PreprocResource]:
        if not VALID_LOGICAL_RESOURCE_ID_RE.match(node_resource.name):
            raise ValidationError(
                f"Template format error: Resource name {node_resource.name} is non alphanumeric."
            )
        change_type = node_resource.change_type
        condition_before = Nothing
        condition_after = Nothing
        if not is_nothing(node_resource.condition_reference):
            condition_delta = self._resolve_resource_condition_reference(
                node_resource.condition_reference
            )
            condition_before = condition_delta.before
            condition_after = condition_delta.after

        depends_on_before = Nothing
        depends_on_after = Nothing
        if not is_nothing(node_resource.depends_on):
            depends_on_delta = self.visit(node_resource.depends_on)
            depends_on_before = depends_on_delta.before
            depends_on_after = depends_on_delta.after

        type_delta = self.visit(node_resource.type_)

        # Check conditions before visiting properties to avoid resolving references
        # (e.g. GetAtt) to conditional resources that were never created.
        should_process_before = change_type != ChangeType.CREATED and (
            is_nothing(condition_before) or condition_before
        )
        should_process_after = change_type != ChangeType.REMOVED and (
            is_nothing(condition_after) or condition_after
        )

        properties_delta: PreprocEntityDelta[PreprocProperties, PreprocProperties]
        if should_process_before or should_process_after:
            properties_delta = self.visit(node_resource.properties)
        else:
            properties_delta = PreprocEntityDelta(before=Nothing, after=Nothing)

        deletion_policy_before = Nothing
        deletion_policy_after = Nothing
        if not is_nothing(node_resource.deletion_policy):
            deletion_policy_delta = self.visit(node_resource.deletion_policy)
            deletion_policy_before = deletion_policy_delta.before
            deletion_policy_after = deletion_policy_delta.after

        update_replace_policy_before = Nothing
        update_replace_policy_after = Nothing
        if not is_nothing(node_resource.update_replace_policy):
            update_replace_policy_delta = self.visit(node_resource.update_replace_policy)
            update_replace_policy_before = update_replace_policy_delta.before
            update_replace_policy_after = update_replace_policy_delta.after

        before = Nothing
        after = Nothing
        if should_process_before:
            logical_resource_id = node_resource.name
            before_physical_resource_id = self._before_resource_physical_id(
                resource_logical_id=logical_resource_id
            )
            before = PreprocResource(
                logical_id=logical_resource_id,
                physical_resource_id=before_physical_resource_id,
                condition=condition_before,
                resource_type=type_delta.before,
                properties=properties_delta.before,
                depends_on=depends_on_before,
                requires_replacement=False,
                deletion_policy=deletion_policy_before,
                update_replace_policy=update_replace_policy_before,
            )
        if should_process_after:
            logical_resource_id = node_resource.name
            try:
                after_physical_resource_id = self._after_resource_physical_id(
                    resource_logical_id=logical_resource_id
                )
            except RuntimeError:
                after_physical_resource_id = None
            after = PreprocResource(
                logical_id=logical_resource_id,
                physical_resource_id=after_physical_resource_id,
                condition=condition_after,
                resource_type=type_delta.after,
                properties=properties_delta.after,
                depends_on=depends_on_after,
                requires_replacement=node_resource.requires_replacement,
                deletion_policy=deletion_policy_after,
                update_replace_policy=update_replace_policy_after,
            )
        return PreprocEntityDelta(before=before, after=after)