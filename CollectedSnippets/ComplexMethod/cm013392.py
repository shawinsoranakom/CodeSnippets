def build_err_msg(
    arrays,
    err_msg,
    header="Items are not equal:",
    verbose=True,
    names=("ACTUAL", "DESIRED"),
    precision=8,
):
    msg = ["\n" + header]
    if err_msg:
        if err_msg.find("\n") == -1 and len(err_msg) < 79 - len(header):
            msg = [msg[0] + " " + err_msg]
        else:
            msg.append(err_msg)
    if verbose:
        for i, a in enumerate(arrays):
            if isinstance(a, ndarray):
                # precision argument is only needed if the objects are ndarrays
                # r_func = partial(array_repr, precision=precision)
                r_func = ndarray.__repr__
            else:
                r_func = repr

            try:
                r = r_func(a)
            except Exception as exc:
                r = f"[repr failed for <{type(a).__name__}>: {exc}]"
            if r.count("\n") > 3:
                r = "\n".join(r.splitlines()[:3])
                r += "..."
            msg.append(f" {names[i]}: {r}")
    return "\n".join(msg)