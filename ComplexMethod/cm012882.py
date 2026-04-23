def _is_match(modules, node, pattern, max_uses=sys.maxsize):
    """Matches a node in fx against a pattern"""
    if isinstance(pattern, tuple):
        self_match, *arg_matches = pattern
        if self_match is getattr:
            if len(pattern) != 2:
                raise AssertionError("Expecting getattr pattern to have two elements")
            arg_matches = []
    else:
        self_match = pattern
        arg_matches = []

    if isinstance(self_match, type) and issubclass(self_match, MatchAllNode):
        return True

    if node == pattern:
        return True

    if not isinstance(node, Node) or len(node.users) > max_uses:
        return False

    if isinstance(self_match, type) and issubclass(self_match, torch.nn.Module):
        if node.op != "call_module":
            return False
        if type_before_parametrizations(modules[node.target]) != self_match:
            return False
    elif callable(self_match):
        if node.op != "call_function" or node.target is not self_match:
            return False
        elif node.target is getattr:
            if node.args[1] != pattern[1]:
                return False
    elif isinstance(self_match, str):
        if node.op != "call_method" or node.target != self_match:
            return False
    elif node.target != self_match:
        return False

    if not arg_matches:
        return True

    if len(arg_matches) != len(node.args):
        return False

    return all(
        _is_match(modules, node, arg_match, max_uses=1)
        for node, arg_match in zip(node.args, arg_matches)
    )