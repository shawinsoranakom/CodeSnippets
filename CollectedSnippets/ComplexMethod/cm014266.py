def helper(
            treespec: PyTreeSpec,
            node: PyTree,
            subtrees: list[PyTree],
        ) -> None:
            if treespec.is_leaf():
                subtrees.append(node)
                return

            node_type = type(node)
            if treespec.type not in BUILTIN_TYPES:
                # Always require custom node types to match exactly
                if node_type != treespec.type:
                    raise ValueError(
                        f"Type mismatch; "
                        f"expected {treespec.type!r}, but got {node_type!r}.",
                    )

                children, metadata, *_ = optree.tree_flatten_one_level(
                    node,
                    none_is_leaf=self.none_is_leaf,
                    namespace=self.namespace,
                )
                if len(children) != treespec.num_children:
                    raise ValueError(
                        f"Node arity mismatch; "
                        f"expected {treespec.num_children}, but got {len(children)}.",
                    )
                if metadata != treespec._metadata:
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
                    expected_keys = treespec.entries()
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
                    children, metadata, *_ = optree.tree_flatten_one_level(
                        node,
                        none_is_leaf=self.none_is_leaf,
                        namespace=self.namespace,
                    )
                    if (
                        node_type is not deque  # ignore mismatch of `maxlen` for deque
                    ) and metadata != treespec._metadata:
                        raise ValueError(
                            f"Node metadata mismatch for node type {treespec.type!r}; "
                            f"expected {treespec._metadata!r}, but got {metadata!r}.",  # namedtuple type mismatch
                        )

            for subtree, subspec in zip(children, treespec._children, strict=True):
                helper(subspec, subtree, subtrees)