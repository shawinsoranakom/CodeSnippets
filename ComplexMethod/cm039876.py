def generate_valid_param(constraint):
    """Return a value that does satisfy a constraint.

    This is only useful for testing purpose.

    Parameters
    ----------
    constraint : Constraint instance
        The constraint to generate a value for.

    Returns
    -------
    val : object
        A value that does satisfy the constraint.
    """
    if isinstance(constraint, _ArrayLikes):
        return np.array([1, 2, 3])

    if isinstance(constraint, _SparseMatrices):
        return csr_array([[0, 1], [1, 0]])

    if isinstance(constraint, _RandomStates):
        return np.random.RandomState(42)

    if isinstance(constraint, _Callables):
        return lambda x: x

    if isinstance(constraint, _NoneConstraint):
        return None

    if isinstance(constraint, _InstancesOf):
        if constraint.type is np.ndarray:
            # special case for ndarray since it can't be instantiated without arguments
            return np.array([1, 2, 3])

        if constraint.type in (Integral, Real):
            # special case for Integral and Real since they are abstract classes
            return 1

        return constraint.type()

    if isinstance(constraint, _Booleans):
        return True

    if isinstance(constraint, _VerboseHelper):
        return 1

    if isinstance(constraint, MissingValues) and constraint.numeric_only:
        return np.nan

    if isinstance(constraint, MissingValues) and not constraint.numeric_only:
        return "missing"

    if isinstance(constraint, HasMethods):
        return type(
            "ValidHasMethods", (), {m: lambda self: None for m in constraint.methods}
        )()

    if isinstance(constraint, _IterablesNotString):
        return [1, 2, 3]

    if isinstance(constraint, _CVObjects):
        return 5

    if isinstance(constraint, Options):  # includes StrOptions
        for option in constraint.options:
            return option

    if isinstance(constraint, Interval):
        interval = constraint
        if interval.left is None and interval.right is None:
            return 0
        elif interval.left is None:
            return interval.right - 1
        elif interval.right is None:
            return interval.left + 1
        else:
            if interval.type is Real:
                return (interval.left + interval.right) / 2
            else:
                return interval.left + 1

    raise ValueError(f"Unknown constraint type: {constraint}")