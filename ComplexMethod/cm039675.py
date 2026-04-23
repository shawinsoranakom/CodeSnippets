def check_cv(cv=5, y=None, *, classifier=False, shuffle=False, random_state=None):
    """Input checker utility for building a cross-validator.

    Parameters
    ----------
    cv : int, cross-validation generator, iterable or None, default=5
        Determines the cross-validation splitting strategy.
        Possible inputs for cv are:
        - None, to use the default 5-fold cross validation,
        - integer, to specify the number of folds,
        - :term:`CV splitter`,
        - an iterable that generates (train, test) splits as arrays of indices.

        For integer/None inputs, if classifier is True and ``y`` is either
        binary or multiclass, :class:`StratifiedKFold` is used. In all other
        cases, :class:`KFold` is used.

        Refer :ref:`User Guide <cross_validation>` for the various
        cross-validation strategies that can be used here.

        .. versionchanged:: 0.22
            ``cv`` default value changed from 3-fold to 5-fold.

    y : array-like, default=None
        The target variable for supervised learning problems.

    classifier : bool, default=False
        Whether the task is a classification task. When ``True`` and `cv` is an
        integer or ``None``, :class:`StratifiedKFold` is used if ``y`` is binary
        or multiclass; otherwise :class:`KFold` is used. Ignored if `cv` is a
        cross-validator instance or iterable.

    shuffle : bool, default=False
        Whether to shuffle the data before splitting into batches. Note that the samples
        within each split will not be shuffled. Only applies if `cv` is an int or
        `None`. If `cv` is a cross-validation generator or an iterable, `shuffle` is
        ignored.

    random_state : int, RandomState instance or None, default=None
        When `shuffle` is True and `cv` is an integer or `None`, `random_state` affects
        the ordering of the indices, which controls the randomness of each fold.
        Otherwise, this parameter has no effect.
        Pass an int for reproducible output across multiple function calls.
        See :term:`Glossary <random_state>`.

    Returns
    -------
    checked_cv : a cross-validator instance.
        The return value is a cross-validator which generates the train/test
        splits via the ``split`` method.

    Examples
    --------
    >>> from sklearn.model_selection import check_cv
    >>> check_cv(cv=5, y=None, classifier=False)
    KFold(...)
    >>> check_cv(cv=5, y=[1, 1, 0, 0, 0, 0], classifier=True)
    StratifiedKFold(...)
    """
    cv = 5 if cv is None else cv
    if isinstance(cv, numbers.Integral):
        if (
            classifier
            and (y is not None)
            and (type_of_target(y, input_name="y") in ("binary", "multiclass"))
        ):
            return StratifiedKFold(cv, shuffle=shuffle, random_state=random_state)
        else:
            return KFold(cv, shuffle=shuffle, random_state=random_state)

    if not hasattr(cv, "split") or isinstance(cv, str):
        if not isinstance(cv, Iterable) or isinstance(cv, str):
            raise ValueError(
                "Expected `cv` as an integer, a cross-validation object "
                "(from sklearn.model_selection), or an iterable yielding (train, test) "
                f"splits as arrays of indices. Got {cv}."
            )
        return _CVIterableWrapper(cv)

    return cv