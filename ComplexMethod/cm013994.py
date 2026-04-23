def check_signature_rewritable(graph: torch.fx.GraphModule) -> None:
    # pyrefly: ignore [implicit-any]
    input_errors = []
    for node in graph.graph.find_nodes(op="placeholder"):
        # set in OutputGraph._call_user_compiler
        assert hasattr(node, "_dynamo_source")
        assert hasattr(graph, "_source_to_user_stacks")

        # NOTE: We can safely ignore these type warnings if and only if
        # the function is made from OutputGraph (checked in the assertions)
        source = node._dynamo_source  # type: ignore[attr-defined]
        user_stacks = graph._source_to_user_stacks.get(source)  # type: ignore[operator, union-attr]
        if user_stacks is None:
            continue
        assert len(user_stacks) > 0
        # In some cases we may not have a useful stack.  Look for a
        # useful stack
        stack = None
        for s in user_stacks:
            if len(s) == 0:
                continue
            stack = s
            break
        if stack is None:
            msg = f"{source.name}, a closed over free variable"
        else:
            tb = "".join(traceback.format_list(stack))
            extra = ""
            if len(user_stacks) > 1:
                extra = f"(elided {len(user_stacks) - 1} more accesses)"
            msg = f"{source.name}, accessed at:\n{tb}{extra}"
        # TODO: option to print ALL of the stack traces at once
        input_errors.append(msg)

    if input_errors:
        raise UserError(
            UserErrorType.INVALID_INPUT,
            "Cannot export model which references tensors that are neither "
            "buffers/parameters/constants nor are direct inputs.  For each tensor, if you'd "
            "like this tensor to be an explicit input, add it as a dummy argument "
            "to the top-level model definition you are exporting; if you would "
            "like its value to be embedded as an exported constant, wrap its access "
            "in a function marked with @assume_constant_result.\n\n"
            + "\n\n".join(input_errors),
        )