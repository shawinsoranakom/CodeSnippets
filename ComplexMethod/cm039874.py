def make_constraint(constraint):
    """Convert the constraint into the appropriate Constraint object.

    Parameters
    ----------
    constraint : object
        The constraint to convert.

    Returns
    -------
    constraint : instance of _Constraint
        The converted constraint.
    """
    if isinstance(constraint, str) and constraint == "array-like":
        return _ArrayLikes()
    if isinstance(constraint, str) and constraint == "sparse matrix":
        return _SparseMatrices()
    if isinstance(constraint, str) and constraint == "random_state":
        return _RandomStates()
    if constraint is callable:
        return _Callables()
    if constraint is None:
        return _NoneConstraint()
    if isinstance(constraint, type):
        return _InstancesOf(constraint)
    if isinstance(
        constraint, (Interval, StrOptions, Options, HasMethods, MissingValues)
    ):
        return constraint
    if isinstance(constraint, str) and constraint == "boolean":
        return _Booleans()
    if isinstance(constraint, str) and constraint == "verbose":
        return _VerboseHelper()
    if isinstance(constraint, str) and constraint == "cv_object":
        return _CVObjects()
    if isinstance(constraint, Hidden):
        constraint = make_constraint(constraint.constraint)
        constraint.hidden = True
        return constraint
    if (isinstance(constraint, str) and constraint == "nan") or (
        isinstance(constraint, float) and np.isnan(constraint)
    ):
        return _NanConstraint()
    raise ValueError(f"Unknown constraint type: {constraint}")