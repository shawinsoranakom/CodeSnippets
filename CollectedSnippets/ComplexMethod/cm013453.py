def _build_proxy_for_sym_expr(
    tracer: _ProxyTracer, expr: sympy.Expr, out: PySymType | None = None
) -> IntLikeType | FloatLikeType | BoolLikeType | None:
    """
    Decompose `expr` and look for the pieces as inputs. If `out` is provided
    then that will be the resulting SymNode (and `out.expr` must be the same as
    `expr`).

    This function is used when the ProxyTorchDispatchMode sees a SymNode
    that it hasn't seen before to try to associate it with traced inputs.

    How can this happen?

    First thing to remember is that although sympy.Exprs are interned (so
    `sympy.Expr("s3*s4")` will always have the same `id` and will always compare
    equal) SymNode does not (so doing `SymNode("s3")*SymNode("s4")` twice in a
    row will give two unique SymNodes).

    - On way for this to happen is if we turn off tracing to compute an
      intermediate value and then USE that value with tracing turned on - for
      example if we turn off tracing to do some FakeTensor propagation to
      compute a size (dtensor does this) but then turn tracing back on and use
      that computed size.

    - Another way is if we compute a size in one graph and stash it somewhere
      hidden (such as in some meta-data) and later use it in a different graph
      (dtensor does this too). Since the size was computed in the first graph
      and it's not an official input to the second graph it's not tracked
      properly. This is often going to show up as it usually works in fullgraph
      but a graph break causes a failure.

    To handle this we decompose the sympy.Expr and look for the pieces as
    inputs. But there are problems with this approach:

    - We lose operation provanance: We end up figuring out where to get the
      inputs - but those may not actually be correct. If we have "s1" coming in
      from both tensor1 and tensor2 and we pick the wrong one we could end up
      keeping a tensor alive longer than intended.

    - There's no guarantee that those values are inputs to the graph: If we have
      "s1*s2" computed in a graph #1 and used in graph #2 there's no guarantee
      that the input that holds "s1" is actually an input on graph #2.

    - The decomposition isn't guaranteed to be the same: Sympy can "simplify"
      expressions so it's possible that our inputs are "s1*s2" and "s3" but we
      decompose it into "s1" and "s2*s3" - which wouldn't be found.

    Other ways we could handle this:

    - Don't: Just require that all inputs are tracked properly. This is the
      "correct" solution but harder because you need to track down each
      potential problem one by one and fix them. And when it fails it's a lot of
      work to figure out both why it's failing and the right way to fix it. This
      is complicated by the fact that a stashed value could be incorrect but
      work fine until we happen to get an graph break in the wrong place - so it
      may be a while before the bug is found. (Maybe we need a "dynamo abuse
      mode" where we run tests with as many graph breaks inserted as possible?)

    - Track SymNode ops separately from proxy tracing: Right now SymNode
      operations are tracked as part of the proxy tracing - so when we disable
      proxy tracing we also disable SymNode tracing. But we don't have to do
      that - we could instead always have SymNodes track where they came from
      and just use that when needed. This solves the problem of tracing being
      temporarily turned off but doesn't help if an input isn't present after a
      graph break.

    - Better decomposition: Right now the decomposition is pretty simple. We do
      have a sat-solver available to us so we could theoretically do a better
      job figuring out a "correct" decomposition. But that still relies on
      having the inputs available at all - which isn't a guarantee.
    """

    if (value := tracer.sympy_expr_tracker.get(expr)) is not None:
        if out:
            raise AssertionError(
                "out should be empty when expr is in sympy_expr_tracker"
            )
        return value.value

    if isinstance(expr, (int, float, bool)):
        return expr
    if expr.is_Integer:
        return int(expr)
    if expr.is_Float:
        return float(expr)

    args = []
    for arg in expr.args:
        if (arg_value := _build_proxy_for_sym_expr(tracer, arg)) is None:
            return None
        args.append(arg_value)

    func: OpOverload | None = _sympy_handlers().get(expr.func)  # type: ignore[assignment]
    if not func:
        return None

    if out is None:
        out = func(*args)
    else:
        _sym_register(tracer, func, tuple(args), out)
    return out