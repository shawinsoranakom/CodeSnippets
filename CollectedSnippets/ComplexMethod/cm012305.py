def apply_gumbel_max_trick(match: Match, softmax, rand_exp):
    if not torch._inductor.config.apply_gumbel_max_trick:
        return

    if (
        rand_exp.op != "call_method"
        or rand_exp.target != "exponential_"
        or len(rand_exp.users) != 1
    ):
        return

    empty_node, rate = rand_exp.args
    if rate != 1.0:
        return

    if len(empty_node.users) != 1:
        return

    if (
        softmax.op != "call_function"
        or softmax.target != torch.nn.functional.softmax
        or len(softmax.users) != 1
    ):
        return
    logits = softmax.args[0]

    truediv, argmax = match.nodes
    nodes_to_erase = [truediv, softmax]

    graph = match.graph

    with graph.inserting_before(argmax):
        log = graph.call_function(torch.log, (rand_exp,))
        gumbel_noise = graph.call_function(operator.neg, (log,))
        argmax_input = graph.call_function(operator.add, (logits, gumbel_noise))
        # pyrefly: ignore [missing-attribute]
        argmax.args[0].replace_all_uses_with(argmax_input)

    # erase nodes
    for n in nodes_to_erase:
        match.graph.erase_node(n)

    counters["inductor"]["apply_gumbel_max_trick"] += 1