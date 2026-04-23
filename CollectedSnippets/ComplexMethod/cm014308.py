def helper(treespec: TreeSpec, node: PyTree, subtrees: list[PyTree]) -> None:
            if treespec.is_leaf():
                subtrees.append(node)
                return

            node_type = _get_node_type(node)
            if treespec.type not in BUILTIN_TYPES:
                # Always require custom node types to match exactly
                if node_type != treespec.type:
                    raise ValueError(
                        f"Type mismatch; "
                        f"expected {treespec.type!r}, but got {node_type!r}.",
                    )
                flatten_fn = SUPPORTED_NODES[node_type].flatten_fn
                children, context = flatten_fn(node)
                if len(children) != treespec.num_children:
                    raise ValueError(
                        f"Node arity mismatch; "
                        f"expected {treespec.num_children}, but got {len(children)}.",
                    )
                if context != treespec._context:
                    raise ValueError(
                        f"Node context mismatch for custom node type {treespec.type!r}.",
                    )
            else:
                # For builtin dictionary types, we allow some flexibility
                # Otherwise, we require exact matches
                both_standard_dict = (
                    treespec.type in STANDARD_DICT_TYPES
                    and node_type in STANDARD_DICT_TYPES
                )
                if not both_standard_dict and node_type != treespec.type:
                    raise ValueError(
                        f"Node type mismatch; "
                        f"expected {treespec.type!r}, but got {node_type!r}.",
                    )
                if len(node) != treespec.num_children:
                    raise ValueError(
                        f"Node arity mismatch; "
                        f"expected {treespec.num_children}, but got {len(node)}.",
                    )

                if both_standard_dict:
                    # dictionary types are compatible with each other
                    dict_context = (
                        treespec._context
                        if treespec.type is not defaultdict
                        # ignore mismatch of `default_factory` for defaultdict
                        else treespec._context[1]
                    )
                    expected_keys = dict_context
                    got_key_set = set(node)
                    expected_key_set = set(expected_keys)
                    if got_key_set != expected_key_set:
                        missing_keys = expected_key_set.difference(got_key_set)
                        extra_keys = got_key_set.difference(expected_key_set)
                        message = ""
                        if missing_keys:
                            message += f"; missing key(s): {missing_keys}"
                        if extra_keys:
                            message += f"; extra key(s): {extra_keys}"
                        raise ValueError(f"Node keys mismatch{message}.")
                    children = [node[key] for key in expected_keys]
                else:
                    # node_type is treespec.type
                    flatten_fn = SUPPORTED_NODES[node_type].flatten_fn
                    children, context = flatten_fn(node)
                    if (
                        node_type is not deque  # ignore mismatch of `maxlen` for deque
                    ) and context != treespec._context:
                        raise ValueError(
                            f"Node context mismatch for node type {treespec.type!r}; "
                            f"expected {treespec._context!r}, but got {context!r}.",  # namedtuple type mismatch
                        )

            for subtree, subspec in zip(children, treespec._children, strict=True):
                helper(subspec, subtree, subtrees)