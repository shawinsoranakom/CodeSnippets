def assert_array_compare(
    comparison,
    x,
    y,
    err_msg="",
    verbose=True,
    header="",
    precision=6,
    equal_nan=True,
    equal_inf=True,
    *,
    strict=False,
):
    __tracebackhide__ = True  # Hide traceback for py.test
    from torch._numpy import all, array, asarray, bool_, inf, isnan, max

    x = asarray(x)
    y = asarray(y)

    def array2string(a):
        return str(a)

    # original array for output formatting
    ox, oy = x, y

    def func_assert_same_pos(x, y, func=isnan, hasval="nan"):
        """Handling nan/inf.

        Combine results of running func on x and y, checking that they are True
        at the same locations.

        """
        __tracebackhide__ = True  # Hide traceback for py.test
        x_id = func(x)
        y_id = func(y)
        # We include work-arounds here to handle three types of slightly
        # pathological ndarray subclasses:
        # (1) all() on `masked` array scalars can return masked arrays, so we
        #     use != True
        # (2) __eq__ on some ndarray subclasses returns Python booleans
        #     instead of element-wise comparisons, so we cast to bool_() and
        #     use isinstance(..., bool) checks
        # (3) subclasses with bare-bones __array_function__ implementations may
        #     not implement np.all(), so favor using the .all() method
        # We are not committed to supporting such subclasses, but it's nice to
        # support them if possible.
        if (x_id == y_id).all().item() is not True:
            msg = build_err_msg(
                [x, y],
                err_msg + f"\nx and y {hasval} location mismatch:",
                verbose=verbose,
                header=header,
                names=("x", "y"),
                precision=precision,
            )
            raise AssertionError(msg)
        # If there is a scalar, then here we know the array has the same
        # flag as it everywhere, so we should return the scalar flag.
        if isinstance(x_id, bool) or x_id.ndim == 0:
            return bool_(x_id)
        elif isinstance(y_id, bool) or y_id.ndim == 0:
            return bool_(y_id)
        else:
            return y_id

    try:
        if strict:
            cond = x.shape == y.shape and x.dtype == y.dtype
        else:
            cond = (x.shape == () or y.shape == ()) or x.shape == y.shape
        if not cond:
            if x.shape != y.shape:
                reason = f"\n(shapes {x.shape}, {y.shape} mismatch)"
            else:
                reason = f"\n(dtypes {x.dtype}, {y.dtype} mismatch)"
            msg = build_err_msg(
                [x, y],
                err_msg + reason,
                verbose=verbose,
                header=header,
                names=("x", "y"),
                precision=precision,
            )
            raise AssertionError(msg)

        flagged = bool_(False)

        if equal_nan:
            flagged = func_assert_same_pos(x, y, func=isnan, hasval="nan")

        if equal_inf:
            flagged |= func_assert_same_pos(
                x, y, func=lambda xy: xy == +inf, hasval="+inf"
            )
            flagged |= func_assert_same_pos(
                x, y, func=lambda xy: xy == -inf, hasval="-inf"
            )

        if flagged.ndim > 0:
            x, y = x[~flagged], y[~flagged]
            # Only do the comparison if actual values are left
            if x.size == 0:
                return
        elif flagged:
            # no sense doing comparison if everything is flagged.
            return

        val = comparison(x, y)

        if isinstance(val, bool):
            cond = val
            reduced = array([val])
        else:
            reduced = val.ravel()
            cond = reduced.all()

        # The below comparison is a hack to ensure that fully masked
        # results, for which val.ravel().all() returns np.ma.masked,
        # do not trigger a failure (np.ma.masked != True evaluates as
        # np.ma.masked, which is falsy).
        if not cond:
            n_mismatch = reduced.size - int(reduced.sum(dtype=intp))
            n_elements = flagged.size if flagged.ndim != 0 else reduced.size
            percent_mismatch = 100 * n_mismatch / n_elements
            remarks = [
                f"Mismatched elements: {n_mismatch} / {n_elements} ({percent_mismatch:.3g}%)"
            ]

            # with errstate(all='ignore'):
            # ignore errors for non-numeric types
            with contextlib.suppress(TypeError, RuntimeError):
                error = abs(x - y)
                if np.issubdtype(x.dtype, np.unsignedinteger):
                    error2 = abs(y - x)
                    np.minimum(error, error2, out=error)
                max_abs_error = max(error)
                remarks.append(
                    "Max absolute difference: " + array2string(max_abs_error.item())
                )

                # note: this definition of relative error matches that one
                # used by assert_allclose (found in np.isclose)
                # Filter values where the divisor would be zero
                nonzero = bool_(y != 0)
                if all(~nonzero):
                    max_rel_error = array(inf)
                else:
                    max_rel_error = max(error[nonzero] / abs(y[nonzero]))
                remarks.append(
                    "Max relative difference: " + array2string(max_rel_error.item())
                )

            err_msg += "\n" + "\n".join(remarks)
            msg = build_err_msg(
                [ox, oy],
                err_msg,
                verbose=verbose,
                header=header,
                names=("x", "y"),
                precision=precision,
            )
            raise AssertionError(msg)
    except ValueError:
        import traceback

        efmt = traceback.format_exc()
        header = f"error during assertion:\n\n{efmt}\n\n{header}"

        msg = build_err_msg(
            [x, y],
            err_msg,
            verbose=verbose,
            header=header,
            names=("x", "y"),
            precision=precision,
        )
        raise ValueError(msg)