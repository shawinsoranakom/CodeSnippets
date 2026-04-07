def resetcycle(parser, token):
    """
    Reset a cycle tag.

    If an argument is given, reset the last rendered cycle tag whose name
    matches the argument, else reset the last rendered cycle tag (named or
    unnamed).
    """
    args = token.split_contents()

    if len(args) > 2:
        raise TemplateSyntaxError("%r tag accepts at most one argument." % args[0])

    if len(args) == 2:
        name = args[1]
        try:
            return ResetCycleNode(parser._named_cycle_nodes[name])
        except (AttributeError, KeyError):
            raise TemplateSyntaxError("Named cycle '%s' does not exist." % name)
    try:
        return ResetCycleNode(parser._last_cycle_node)
    except AttributeError:
        raise TemplateSyntaxError("No cycles in template.")