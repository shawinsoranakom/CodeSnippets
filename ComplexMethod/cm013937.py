def visit_dict_manager(node: DictGuardManager) -> list[GuardManager]:
            # Just recurse through the key and value dict managers and check if
            # all of them are tag safe nodes.
            assert issubclass(node.get_type_of_guarded_value(), dict)

            tag_safe_roots = []
            is_subtree_tag_safe = True

            # Recurse to get the tag safe roots from subtree.
            for _idx, (key_mgr, val_mgr) in sorted(
                node.get_key_value_managers().items()
            ):
                if key_mgr is not None:
                    visit(key_mgr)
                if val_mgr is not None:
                    tag_safe_roots.extend(visit(val_mgr))

            for key_mgr, val_mgr in node.get_key_value_managers().values():
                if key_mgr:
                    is_subtree_tag_safe &= key_mgr.is_tag_safe()

                if val_mgr:
                    is_subtree_tag_safe &= val_mgr.is_tag_safe()

            if is_subtree_tag_safe:
                node.mark_tag_safe()
            return tag_safe_roots