def matches(modules, node, pattern, max_uses=sys.maxsize):
    if isinstance(pattern, tuple):
        self_match, *arg_matches = pattern
    else:
        self_match = pattern
        arg_matches = None

    if len(node.users) > max_uses:
        return False

    if isinstance(self_match, type) and issubclass(self_match, torch.nn.Module):
        if node.op != "call_module":
            return False
        if not isinstance(modules[node.target], self_match):
            return False
    elif callable(self_match):
        if node.op != "call_function" or node.target is not self_match:
            return False
    elif node.target != self_match:
        return False

    if not arg_matches:
        return True

    if len(arg_matches) != len(node.args):
        return False

    return all(
        matches(modules, node, arg_match, max_uses=1)
        for node, arg_match in zip(node.args, arg_matches)
    )