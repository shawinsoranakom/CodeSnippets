def _visit_resource(
        self,
        scope: Scope,
        resource_name: str,
        before_resource: Maybe[dict],
        after_resource: Maybe[dict],
    ) -> NodeResource:
        node_resource = self._visited_scopes.get(scope)
        if isinstance(node_resource, NodeResource):
            return node_resource

        scope_type, (before_type, after_type) = self._safe_access_in(
            scope, TypeKey, before_resource, after_resource
        )
        terminal_value_type = self._visit_type(
            scope=scope_type, before_type=before_type, after_type=after_type
        )

        condition_reference = Nothing
        scope_condition, (before_condition, after_condition) = self._safe_access_in(
            scope, ConditionKey, before_resource, after_resource
        )
        if before_condition or after_condition:
            condition_reference = self._visit_terminal_value(
                scope_condition, before_condition, after_condition
            )

        depends_on = Nothing
        scope_depends_on, (before_depends_on, after_depends_on) = self._safe_access_in(
            scope, DependsOnKey, before_resource, after_resource
        )
        if before_depends_on or after_depends_on:
            depends_on = self._visit_depends_on(
                scope_depends_on, before_depends_on, after_depends_on
            )

        scope_properties, (before_properties, after_properties) = self._safe_access_in(
            scope, PropertiesKey, before_resource, after_resource
        )
        properties = self._visit_properties(
            scope=scope_properties,
            before_properties=before_properties,
            after_properties=after_properties,
        )

        deletion_policy = Nothing
        scope_deletion_policy, (before_deletion_policy, after_deletion_policy) = (
            self._safe_access_in(scope, DeletionPolicyKey, before_resource, after_resource)
        )
        if before_deletion_policy or after_deletion_policy:
            deletion_policy = self._visit_deletion_policy(
                scope_deletion_policy, before_deletion_policy, after_deletion_policy
            )

        update_replace_policy = Nothing
        scope_update_replace_policy, (before_update_replace_policy, after_update_replace_policy) = (
            self._safe_access_in(scope, UpdateReplacePolicyKey, before_resource, after_resource)
        )
        if before_update_replace_policy or after_update_replace_policy:
            update_replace_policy = self._visit_update_replace_policy(
                scope_update_replace_policy,
                before_update_replace_policy,
                after_update_replace_policy,
            )

        fn_transform = Nothing
        scope_fn_transform, (before_fn_transform_args, after_fn_transform_args) = (
            self._safe_access_in(scope, FnTransform, before_resource, after_resource)
        )
        if not is_nothing(before_fn_transform_args) or not is_nothing(after_fn_transform_args):
            if scope_fn_transform.count(FnTransform) > 1:
                raise RuntimeError(
                    "Invalid: Fn::Transforms cannot be nested inside another Fn::Transform"
                )
            path = "$" + ".".join(scope_fn_transform.split("/")[:-1])
            before_siblings = extract_jsonpath(self._before_template, path)
            after_siblings = extract_jsonpath(self._after_template, path)
            arguments_scope = scope.open_scope("args")
            arguments = self._visit_value(
                scope=arguments_scope,
                before_value=before_fn_transform_args,
                after_value=after_fn_transform_args,
            )
            fn_transform = NodeIntrinsicFunctionFnTransform(
                scope=scope_fn_transform,
                change_type=ChangeType.MODIFIED,  # TODO
                arguments=arguments,  # TODO
                intrinsic_function=FnTransform,
                before_siblings=before_siblings,
                after_siblings=after_siblings,
            )

        change_type = change_type_of(
            before_resource,
            after_resource,
            [
                properties,
                condition_reference,
                depends_on,
                deletion_policy,
                update_replace_policy,
                fn_transform,
            ],
        )

        # special case of where either the before or after state does not specify properties but
        # the resource was in the previous template
        if (
            terminal_value_type.change_type == ChangeType.UNCHANGED
            and properties.change_type != ChangeType.UNCHANGED
        ):
            change_type = ChangeType.MODIFIED

        requires_replacement = self._resolve_requires_replacement(
            node_properties=properties, resource_type=terminal_value_type
        )
        node_resource = NodeResource(
            scope=scope,
            change_type=change_type,
            name=resource_name,
            type_=terminal_value_type,
            properties=properties,
            condition_reference=condition_reference,
            depends_on=depends_on,
            requires_replacement=requires_replacement,
            deletion_policy=deletion_policy,
            update_replace_policy=update_replace_policy,
            fn_transform=fn_transform,
        )
        self._visited_scopes[scope] = node_resource
        return node_resource