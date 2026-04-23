def fuzz_op(
    target_spec: Spec,
    depth,
    stack_size,
    template: str = "default",
    supported_ops: list[str] | None = None,
) -> tuple[str, list[Spec]]:
    """
    Given an output specification, returns an operation that can
    produce a tensor with that layout using the operator class system.

    Args:
        target_spec: Desired output specification (TensorSpec or ScalarSpec)
        depth: Maximum depth for operation generation. At depth 0, only leaf operations
               (constant, arg) are allowed. Higher depths allow more complex operations.
        stack_size: Current stack size. When < 10, reduces probability of leaf operations.

    Returns:
        Tuple of (operation_name, list_of_argument_specs) where each argument spec
        describes the layout requirements for the operation's inputs
    """
    # Get template-filtered operators
    available_operators = _get_template_filtered_operators(template, supported_ops)

    # Filter operators that can produce the target spec
    # IMPORTANT: iterate in a deterministic order to avoid dict-order nondeterminism
    compatible_ops = []
    for op_name in sorted(available_operators.keys()):
        operator = available_operators[op_name]
        if operator.can_produce(target_spec):
            compatible_ops.append((op_name, operator))

    # Shuffle with seeded RNG (caller seeds random), but from a deterministic base order
    random.shuffle(compatible_ops)

    if not compatible_ops:
        raise ValueError(f"No operators available that can produce {target_spec}")

    # Categorize operators into leaf and non-leaf
    leaf_ops = []
    non_leaf_ops = []

    for op_name, operator in compatible_ops:
        if op_name in ["constant", "arg"] or op_name.startswith("arg_"):
            leaf_ops.append((op_name, operator))
        else:
            non_leaf_ops.append((op_name, operator))

    # Choose operation based on depth and stack size constraints
    if depth == 0:
        # At depth 0, only allow leaf operations
        if not leaf_ops:
            # If no leaf ops can produce this spec, fallback to arg
            return _get_arg_args_specs(target_spec)
        # Weighted choice among leaf ops
        leaf_weights = [
            op.get_weight(
                target_spec=target_spec,
                depth=depth,
                stack_size=stack_size,
                template=template,
            )
            for _, op in leaf_ops
        ]
        idx = random.choices(range(len(leaf_ops)), weights=leaf_weights, k=1)[0]
        chosen_op_name, chosen_operator = leaf_ops[idx]
    else:
        # At higher depths, choose between leaf and non-leaf operations
        # Reduce probability of leaf operations when stack_size < 10
        if (stack_size < 10 or depth > 7) and non_leaf_ops:
            # 80% chance of non-leaf, 20% chance of leaf
            if random.random() < 0.8:
                # Weighted choice among non-leaf ops
                nonleaf_weights = [
                    op.get_weight(
                        target_spec=target_spec,
                        depth=depth,
                        stack_size=stack_size,
                        template=template,
                    )
                    for _, op in non_leaf_ops
                ]
                idx = random.choices(
                    range(len(non_leaf_ops)), weights=nonleaf_weights, k=1
                )[0]
                chosen_op_name, chosen_operator = non_leaf_ops[idx]
            else:
                if leaf_ops:
                    leaf_weights = [
                        op.get_weight(
                            target_spec=target_spec,
                            depth=depth,
                            stack_size=stack_size,
                            template=template,
                        )
                        for _, op in leaf_ops
                    ]
                    idx = random.choices(
                        range(len(leaf_ops)), weights=leaf_weights, k=1
                    )[0]
                    chosen_op_name, chosen_operator = leaf_ops[idx]
                else:
                    nonleaf_weights = [
                        op.get_weight(
                            target_spec=target_spec,
                            depth=depth,
                            stack_size=stack_size,
                            template=template,
                        )
                        for _, op in non_leaf_ops
                    ]
                    idx = random.choices(
                        range(len(non_leaf_ops)), weights=nonleaf_weights, k=1
                    )[0]
                    chosen_op_name, chosen_operator = non_leaf_ops[idx]
        else:
            # Normal probability distribution over all ops
            all_ops = non_leaf_ops + leaf_ops
            if all_ops:
                all_weights = [
                    op.get_weight(
                        target_spec=target_spec,
                        depth=depth,
                        stack_size=stack_size,
                        template=template,
                    )
                    for _, op in all_ops
                ]
                idx = random.choices(range(len(all_ops)), weights=all_weights, k=1)[0]
                chosen_op_name, chosen_operator = all_ops[idx]
            else:
                chosen_op_name, chosen_operator = ("arg", get_operator("arg"))

    if chosen_operator is None:
        # If no operator found, fallback to arg
        return _get_arg_args_specs(target_spec)

    input_specs = chosen_operator.fuzz_inputs_specs(target_spec)
    return chosen_op_name, input_specs