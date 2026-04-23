def parse(op: str) -> BaseOperatorName:
        if op == "":
            raise AssertionError("operator name cannot be empty")
        if op.endswith("_out"):
            raise AssertionError(
                "_out suffix is reserved and not permitted for operator names; "
                "did you mean to specify an out overload name instead?"
            )
        # Extract namespace out. Base operator name may or may not contain namespace.
        # E.g., aten::__lshift__ is a valid base operator name, __lshift__ is also valid.
        # We want to split the namespace out from the base operator name.
        match = re.match(r"^(?:(.*)::)?(.*)$", op)
        namespace = match.group(1) if match else ""
        op_without_ns = match.group(2) if match else op
        m = re.match(r"^__([^_]+)__$", op_without_ns)
        if m is not None:
            dunder_method = True
            base = m.group(1)
            if any(base == f"i{n}" for n in AUGMENTED_ASSIGNMENT_NAMES):
                inplace = True
                base = base[1:]
            else:
                inplace = False
                # temporary, this is not intrinsically true but
                # has been historically true for dunder methods
                # we support  (but, if we ever got, say, __int__, this would
                # be wrong!)
                if base[0] == "i":
                    raise AssertionError(
                        f"unexpected dunder method starting with 'i': {op}"
                    )
        else:
            dunder_method = False
            base = op_without_ns
            if base[-1] == "_":
                inplace = True
                base = base[:-1]
            else:
                inplace = False

        # See Note [Overload Ambiguity With Functional Variants]
        functional_suffix = "_functional"
        if base.endswith(functional_suffix):
            functional_overload = True
            base = base[: -len(functional_suffix)]
            # This seems complicated and unnecessary, so banning dunder methods
            # for now on ops that have a functional + mutable variant (like native_batch_norm).
            if dunder_method or inplace:
                raise AssertionError(
                    f"functional overload cannot be a dunder method or inplace: {op}"
                )
        else:
            functional_overload = False

        r = BaseOperatorName(
            base=base,
            inplace=inplace,
            dunder_method=dunder_method,
            functional_overload=functional_overload,
            namespace=namespace,
        )
        if str(r) != op:
            raise AssertionError(f"{str(r)} != {op}")
        return r