def broadcast_types(t1: Any, t2: Any) -> tuple[Any, Any]:
    """
    Applies broadcasting to both given types such that they
    become consistent with each other and returns two new
    resulting types
    """

    # if either type is Dyn, do nothing since the types are already consistent
    if t1 == Dyn or t2 == Dyn or isinstance(t1, Var) or isinstance(t2, Var):
        return t1, t2

    if isinstance(t1, TensorType) and isinstance(t2, TensorType):
        s1 = len(t1.__args__)
        s2 = len(t2.__args__)

        new_t1 = list(t1.__args__)
        new_t2 = list(t2.__args__)

        # We make the types the same length which is the first requirement
        # for consistency
        if s1 > s2:
            for _ in range(s1 - s2):
                new_t2.insert(0, 1)

        elif s2 > s1:
            for _ in range(s2 - s1):
                new_t1.insert(0, 1)

        # we replace occurrences of "1" with each tensor with
        # the corresponding type from the other tensor
        for i, (x, y) in enumerate(zip(new_t1, new_t2)):
            if x == 1:
                new_t1[i] = y
            elif y == 1:
                new_t2[i] = x

        # at this point our tensors should be consistent
        # and we can apply the element-wise operation and find the right dimension
        # for the output of the operation
        (t1, t2) = TensorType(tuple(new_t1)), TensorType(tuple(new_t2))
        return (t1, t2)
    else:
        raise TypeError(f"Cannot broadcast types {t1} and {t2}")