def _visit_value(
        self, scope: Scope, before_value: Maybe[Any], after_value: Maybe[Any]
    ) -> ChangeSetEntity:
        value = self._visited_scopes.get(scope)
        if isinstance(value, ChangeSetEntity):
            return value

        before_type_name = self._type_name_of(before_value)
        after_type_name = self._type_name_of(after_value)
        unset = object()
        if before_type_name == after_type_name:
            dominant_value = before_value
        elif is_created(before=before_value, after=after_value):
            dominant_value = after_value
        elif is_removed(before=before_value, after=after_value):
            dominant_value = before_value
        else:
            dominant_value = unset
        if dominant_value is not unset:
            dominant_type_name = self._type_name_of(dominant_value)
            if self._is_terminal(value=dominant_value):
                value = self._visit_terminal_value(
                    scope=scope, before_value=before_value, after_value=after_value
                )
            elif self._is_object(value=dominant_value):
                value = self._visit_object(
                    scope=scope, before_object=before_value, after_object=after_value
                )
            elif self._is_array(value=dominant_value):
                value = self._visit_array(
                    scope=scope, before_array=before_value, after_array=after_value
                )
            elif self._is_intrinsic_function_name(dominant_type_name):
                intrinsic_function_scope, (before_arguments, after_arguments) = (
                    self._safe_access_in(scope, dominant_type_name, before_value, after_value)
                )
                value = self._visit_intrinsic_function(
                    scope=intrinsic_function_scope,
                    intrinsic_function=dominant_type_name,
                    before_arguments=before_arguments,
                    after_arguments=after_arguments,
                )
            else:
                raise RuntimeError(f"Unsupported type {type(dominant_value)}")
        # Case: type divergence.
        else:
            value = self._visit_divergence(
                scope=scope, before_value=before_value, after_value=after_value
            )
        self._visited_scopes[scope] = value
        return value