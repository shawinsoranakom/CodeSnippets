def visit_manager(node: GuardManager) -> list[GuardManager]:
            assert not isinstance(node, DictGuardManager)

            # Collect the subtree tag safe roots
            tag_safe_roots = []
            for child_mgr in node.get_child_managers():
                tag_safe_roots.extend(visit(child_mgr))

            if node.is_guarded_value_immutable():
                # If the node guards a tensor, mark it tag safe only if there
                # are no accessors. Presence of accessors means presence of
                # symbolic shape guards.
                if issubclass(node.get_type_of_guarded_value(), torch.Tensor):
                    if node.has_no_accessors() and not node.has_object_aliasing_guard():
                        node.mark_tag_safe()
                else:
                    node.mark_tag_safe()
            elif issubclass(node.get_type_of_guarded_value(), dict):
                accessors = node.get_accessors()
                child_mgrs = node.get_child_managers()
                is_subtree_tag_safe = all(
                    isinstance(accessor, DictGetItemGuardAccessor) and mgr.is_tag_safe()
                    for accessor, mgr in zip(accessors, child_mgrs)
                )
                if is_subtree_tag_safe:
                    node.mark_tag_safe()
            elif issubclass(node.get_type_of_guarded_value(), torch.nn.Module):
                is_subtree_tag_safe = check_tag_safety(
                    node, (GetGenericDictGuardAccessor, TypeGuardAccessor)
                )
                if is_subtree_tag_safe:
                    node.mark_tag_safe()
                    # Return the current node as tag safe root, discarding the
                    # subtree tag safe roots.
                    return [
                        node,
                    ]
            elif (
                node.get_type_of_guarded_value()
                in (
                    types.FunctionType,
                    types.MethodType,
                    staticmethod,
                    classmethod,
                )
                and config.assume_dunder_attributes_remain_unchanged
            ):
                # Assumption: callers will not reassignthe attributes
                #   func.__code__, func.__closure__, func.__defaults__, or func.__kwdefaults__.
                # Mutating the objects those attributes point to is fine;
                # rebinding the attribute itself is not.
                # Example ─ allowed:   foo.__defaults__[0].bar = 99
                #          forbidden: foo.__defaults__ = (3, 4)
                is_subtree_tag_safe = check_tag_safety(
                    node,
                    (
                        CodeGuardAccessor,
                        ClosureGuardAccessor,
                        FuncDefaultsGuardAccessor,
                        FuncKwDefaultsGuardAccessor,
                        GetAttrGuardAccessor,
                    ),
                )

                for accessor in node.get_accessors():
                    if isinstance(accessor, GetAttrGuardAccessor):
                        is_subtree_tag_safe &= (
                            accessor.get_attr_name() in dunder_attrs_assumed_constants
                        )

                if is_subtree_tag_safe:
                    node.mark_tag_safe()
            elif issubclass(node.get_type_of_guarded_value(), types.CellType):
                is_subtree_tag_safe = check_tag_safety(node, (GetAttrGuardAccessor,))

                is_subtree_tag_safe &= all(
                    isinstance(accessor, GetAttrGuardAccessor)
                    and accessor.get_attr_name() == "cell_contents"
                    for accessor in node.get_accessors()
                )
                if is_subtree_tag_safe:
                    node.mark_tag_safe()
            elif (
                issubclass(node.get_type_of_guarded_value(), tuple)
                and node.get_source().endswith(dunder_attrs_assumed_constants)
                and config.assume_dunder_attributes_remain_unchanged
            ):
                # We trust tuples obtained from a function's __closure__ or
                # __defaults__. Any *other* tuple-valued attribute can be
                # silently replaced—for example:
                #
                #     foo.bar = (1, 2)      # original
                #     foo.bar = (3, 4)      # rebinding that our dict-tag optimisation won't see
                #
                # Therefore only tuples from __closure__ / __defaults__ participate in the
                # recursive-dict-tag optimization; all others are ignored.
                is_subtree_tag_safe = check_tag_safety(
                    node, (TupleGetItemGuardAccessor,)
                )
                if is_subtree_tag_safe:
                    node.mark_tag_safe()
            elif issubclass(node.get_type_of_guarded_value(), type):
                is_subtree_tag_safe = check_tag_safety(
                    node, (TypeDictGuardAccessor, TypeMROGuardAccessor)
                )
                if is_subtree_tag_safe:
                    node.mark_tag_safe()

            return tag_safe_roots