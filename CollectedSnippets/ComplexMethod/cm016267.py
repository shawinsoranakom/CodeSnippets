def sort_overloads(
    grouped_overloads: Sequence[PythonSignatureGroup], *, symint: bool = True
) -> Sequence[PythonSignatureGroup]:
    # NB: Smaller here means lower priority

    def is_arg_smaller(t1: Type, t2: Type) -> bool:
        return (
            str(t1) == "Scalar"
            and str(t2) == "Tensor"
            or str(t1) == "Scalar?"
            and str(t2) == "Tensor?"
            or "Dimname" in str(t1)
            and "Dimname" not in str(t2)
            or
            # In the discussion https://github.com/pytorch/pytorch/issues/54555 it has been
            # discussed why it is important to prioritize int/int? over int[]
            str(t1) == "int[]"
            and (str(t2) == "int" or str(t2) == "int?")
            or
            # TensorList currently throws an error during argument parsing, that's why it needs to be
            # last in signature ordering. See discussion: https://github.com/pytorch/pytorch/issues/58087
            str(t1) == "Tensor[]"
            and str(t2).find("[]") != -1
            or
            # Prioritize IntArrayRef overload over SymIntArrayRef
            str(t1) == "SymInt[]"
            and str(t2) == "int[]"
            or
            # Make sure both in, SymInt are sorted consistently w.r.t. Tensor since Tensor can be implicitly
            # converted to either int or SymInt.  Prioritize the Tensor overload since it otherwise gets shadowed.
            (str(t1) == "SymInt" or str(t1) == "int")
            and str(t2) == "Tensor"
        )

    def is_smaller(s1: PythonSignature, s2: PythonSignature) -> bool:
        """Returns True if s1 < s2 in the partial order."""
        args1, args2 = s1.arguments(skip_outputs=True), s2.arguments(skip_outputs=True)
        if len(args1) != len(args2):
            return False
        # TODO: should use some canonical form instead of 'str(arg.type)' - see comments
        # above. The old codegen used the deprecated 'dynamic_type(arg.type)', which
        # ignores the optional annotation, i.e. 'Scalar' and 'Scalar?'.
        equal = all(arg1.type == arg2.type for arg1, arg2 in zip(args1, args2))
        smaller_or_equal = all(
            str(arg1.type) == str(arg2.type) or is_arg_smaller(arg1.type, arg2.type)
            for arg1, arg2 in zip(args1, args2)
        )
        return smaller_or_equal and not equal

    # First sort by signature
    grouped_overloads = sorted(
        grouped_overloads, key=lambda x: x.signature.signature_str(symint=symint)
    )

    # Construct the relation graph
    larger_than: dict[int, set[int]] = defaultdict(set)
    for i1, overload1 in enumerate(grouped_overloads):
        for i2, overload2 in enumerate(grouped_overloads):
            if is_smaller(overload1.signature, overload2.signature):
                larger_than[i1].add(i2)

    if not larger_than:
        return list(grouped_overloads)

    # Use a topological sort to sort overloads according to the partial order.
    N = len(grouped_overloads)
    sorted_ids: list[int] = list(filter(lambda x: x not in larger_than, range(N)))

    for idx in range(N):
        # The size of sorted_ids will grow to N eventually.
        i = sorted_ids[idx]
        for j in sorted(larger_than.keys()):
            larger = larger_than[j]
            larger.discard(i)
            if not larger:
                del larger_than[j]
                sorted_ids.append(j)

    return [grouped_overloads[x] for x in sorted_ids]