def check(f, t, delta, check_val=True, graph_input=False):
    if graph_input:
        fx_g = f
    else:
        fx_g = make_fx(f)(t)
    new_graph = fx_graph_cse(fx_g.graph)
    new_g = fx.GraphModule(fx_g, new_graph)

    # the number of nodes decrease/ or stay the same
    old_num_nodes = len(fx_g.graph.nodes)
    new_num_nodes = len(new_graph.nodes)
    if delta == -1:
        if old_num_nodes < new_num_nodes:
            raise AssertionError(
                f"number of nodes increased {old_num_nodes}, {new_num_nodes}"
            )
    else:
        if old_num_nodes != new_num_nodes + delta:
            raise AssertionError(
                f"number of nodes not the same {old_num_nodes - delta}, {new_num_nodes}\n {fx_g.graph} \n {new_graph}"
            )

    # a second pass should not reduce more nodes
    pass_2_graph = fx_graph_cse(new_graph)
    pass_2_num_nodes = len(pass_2_graph.nodes)
    if pass_2_num_nodes != new_num_nodes:
        raise AssertionError(
            f"second pass graph has less node {pass_2_num_nodes}, {new_num_nodes}\n {new_graph} \n {pass_2_graph}"
        )

    # check correctness
    if check_val:
        true_result = fx_g(t)
        our_result = new_g(t)
        if true_result is None:  # both return None
            if our_result is not None:
                raise AssertionError(f"true result is None, CSE result is {our_result}")
        else:  # results returned are the same
            if not torch.all(true_result == our_result):
                raise AssertionError(
                    f"results are different {true_result}, {our_result}"
                )