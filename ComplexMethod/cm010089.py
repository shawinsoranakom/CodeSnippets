def get_operator_enum(reduce_, use_new_options=False):
    if use_new_options:
        if reduce_ == "sum":
            return "REDUCE_ADD"
        elif reduce_ == "prod":
            return "REDUCE_MULTIPLY"
        elif reduce_ == "mean":
            return "REDUCE_MEAN"
        elif reduce_ == "amax":
            return "REDUCE_MAXIMUM"
        elif reduce_ == "amin":
            return "REDUCE_MINIMUM"
        torch._check(
            False,
            lambda: "reduce argument must be either sum, prod, mean, amax or amin.",
        )
        return
    else:
        if reduce_ == "add":
            return "REDUCE_ADD"
        elif reduce_ == "multiply":
            return "REDUCE_MULTIPLY"
        torch._check(False, lambda: "reduce argument must be either add or multiply.")
        return