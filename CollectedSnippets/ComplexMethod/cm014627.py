def return_names(f: NativeFunction, *, fallback_name: str = "result") -> Sequence[str]:
    returns: list[str] = []
    for i, r in enumerate(f.func.returns):
        # If we have an inplace function, the return argument is
        # implicitly named self.
        # TODO: Consider incorporating this into the data model
        if f.func.name.name.inplace:
            if i != 0:
                raise AssertionError("illegal inplace function with multiple returns")
            name = "self"
        # If we are out function, the name is the name of the
        # corresponding output function (r.name will get recorded
        # in field_name later.)
        elif f.func.is_out_fn():
            name = f.func.arguments.out[i].name
        # If the return argument is explicitly named...
        elif r.name:
            name_conflict = any(
                r.name == a.name for a in f.func.schema_order_arguments()
            )
            if name_conflict and not f.func.is_out_fn():
                name = f"{r.name}_return"
            else:
                name = r.name
        # If there is no explicit name and no fallback name was passed in, we just name the output result,
        # unless it's a multi-return, in which case it's result0,
        # result1, etc (zero-indexed)
        else:
            name = fallback_name if len(f.func.returns) == 1 else f"{fallback_name}{i}"
        returns.append(name)
    return returns