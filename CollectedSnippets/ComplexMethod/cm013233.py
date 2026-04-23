def outs_and_grads(fn, graph_inps, inps):
    outs = fn(*graph_inps)
    for out in pytree.tree_leaves(outs):
        if isinstance(out, torch.Tensor) and out.requires_grad:
            out.sum().backward(retain_graph=True)
    grads = [inp.grad for inp in pytree.tree_leaves(inps) if isinstance(inp, torch.Tensor)]
    for inp in pytree.tree_leaves(inps):
        if isinstance(inp, torch.Tensor):
            inp.grad = None
    return outs, grads