def replace_and_collect(current_node, replacement_tensors):
                        """
                        Collect replacements for getitem nodes into replace_dict.
                        Nodes are added in child-first order so children are erased before parents.
                        """
                        # Find all users that are getitem nodes indexing into current_node
                        getitem_users = [
                            u
                            for u in current_node.users
                            if is_getitem_node(u, current_node)
                        ]

                        if not getitem_users:
                            # Leaf node - add to replace_dict with actual replacement
                            if isinstance(replacement_tensors, (list, tuple)):
                                if len(replacement_tensors) == 1:
                                    replace_dict[current_node] = replacement_tensors[0]
                                    return True
                                else:
                                    # Multiple tensors but no indexing - can't replace
                                    return False
                            else:
                                replace_dict[current_node] = replacement_tensors
                                return True

                        # Process children first (so they're added to replace_dict before parent)
                        all_children_replaced = True
                        first_replacement = None
                        for getitem_user in getitem_users:
                            idx = get_index_from_node(getitem_user)
                            if idx is None or not isinstance(idx, int):
                                all_children_replaced = False
                                continue

                            if not isinstance(replacement_tensors, (list, tuple)):
                                all_children_replaced = False
                                continue

                            if idx >= len(replacement_tensors):
                                all_children_replaced = False
                                continue

                            if first_replacement is None:
                                first_replacement = replacement_tensors[idx]

                            if not replace_and_collect(
                                getitem_user, replacement_tensors[idx]
                            ):
                                all_children_replaced = False

                        # Add this node to replace_dict after children (even if it has non-getitem users)
                        # Non-getitem users will have their input replaced via replace_all_uses_with
                        if all_children_replaced and first_replacement is not None:
                            replace_dict[current_node] = first_replacement

                        return all_children_replaced