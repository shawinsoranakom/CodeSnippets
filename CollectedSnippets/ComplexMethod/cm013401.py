def is_consistent(t1: object, t2: object) -> bool:
    """
    A binary relation denoted by ~ that determines if t1 is consistent with t2.
    The relation is reflexive, symmetric but not transitive.
    returns True if t1 and t2 are consistent and False otherwise.
    Example:
        Dyn ~ TensorType((1,2,3))
        int ~ Dyn
        int ~ int
        TensorType((1,Dyn,3)) ~ TensorType((1,2,3))
    """

    if t1 == t2:
        return True

    if t1 == Dyn or t2 == Dyn or isinstance(t1, Var) or isinstance(t2, Var):
        return True

    if isinstance(t1, TensorType) and isinstance(t2, TensorType):
        return len(t1.__args__) == len(t2.__args__) and all(
            is_consistent(elem1, elem2)
            for elem1, elem2 in zip(t1.__args__, t2.__args__)
        )
    else:
        return False