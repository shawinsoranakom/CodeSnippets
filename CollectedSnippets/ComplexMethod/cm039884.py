def _line_search_wolfe12(
    f, fprime, xk, pk, gfk, old_fval, old_old_fval, verbose=0, **kwargs
):
    """
    Same as line_search_wolfe1, but fall back to line_search_wolfe2 if
    suitable step length is not found, and raise an exception if a
    suitable step length is not found.

    Raises
    ------
    _LineSearchError
        If no suitable step size is found.

    """
    is_verbose = verbose >= 2
    eps = 16 * np.finfo(np.asarray(old_fval).dtype).eps
    if is_verbose:
        print("  Line Search")
        print(f"    eps=16 * finfo.eps={eps}")
        print("    try line search wolfe1")

    ret = line_search_wolfe1(f, fprime, xk, pk, gfk, old_fval, old_old_fval, **kwargs)

    if is_verbose:
        _not_ = "not " if ret[0] is None else ""
        print("    wolfe1 line search was " + _not_ + "successful")

    if ret[0] is None:
        # Have a look at the line_search method of our NewtonSolver class. We borrow
        # the logic from there
        # Deal with relative loss differences around machine precision.
        args = kwargs.get("args", tuple())
        fval = f(xk + pk, *args)
        tiny_loss = np.abs(old_fval * eps)
        loss_improvement = fval - old_fval
        check = np.abs(loss_improvement) <= tiny_loss
        if is_verbose:
            print(
                "    check loss |improvement| <= eps * |loss_old|:"
                f" {np.abs(loss_improvement)} <= {tiny_loss} {check}"
            )
        if check:
            # 2.1 Check sum of absolute gradients as alternative condition.
            sum_abs_grad_old = scipy.linalg.norm(gfk, ord=1)
            grad = fprime(xk + pk, *args)
            sum_abs_grad = scipy.linalg.norm(grad, ord=1)
            check = sum_abs_grad < sum_abs_grad_old
            if is_verbose:
                print(
                    "    check sum(|gradient|) < sum(|gradient_old|): "
                    f"{sum_abs_grad} < {sum_abs_grad_old} {check}"
                )
            if check:
                ret = (
                    1.0,  # step size
                    ret[1] + 1,  # number of function evaluations
                    ret[2] + 1,  # number of gradient evaluations
                    fval,
                    old_fval,
                    grad,
                )

    if ret[0] is None:
        # line search failed: try different one.
        # TODO: It seems that the new check for the sum of absolute gradients above
        # catches all cases that, earlier, ended up here. In fact, our tests never
        # trigger this "if branch" here and we can consider to remove it.
        if is_verbose:
            print("    last resort: try line search wolfe2")
        ret = line_search_wolfe2(
            f, fprime, xk, pk, gfk, old_fval, old_old_fval, **kwargs
        )
        if is_verbose:
            _not_ = "not " if ret[0] is None else ""
            print("    wolfe2 line search was " + _not_ + "successful")

    if ret[0] is None:
        raise _LineSearchError()

    return ret