def _replace_invoke_subgraph_node(node, module, output_tokens, input_tokens):
    """Replace an invoke_subgraph node to remove the token argument."""
    if node.args[0].op != "get_attr":
        raise AssertionError(
            f"Expected node.args[0].op to be 'get_attr', but got {node.args[0].op}"
        )
    submod = getattr(module, node.args[0].target)
    if not submod.meta.get("has_with_effects", False):
        return

    # Remove token from inputs
    subgraph, identifier, token, *operands = node.args
    node.args = (subgraph, identifier, *operands)
    if token.op == "placeholder":
        input_tokens.append(token)

    # Update getitem nodes to account for removed token output
    for user in list(node.users.keys()):
        if user.args[1] >= 1:
            user.args = (node, user.args[1] - 1)
        elif user.args[1] == 0:
            for user_user in list(user.users.keys()):
                if user_user.op == "output":
                    output_tokens.append(user)