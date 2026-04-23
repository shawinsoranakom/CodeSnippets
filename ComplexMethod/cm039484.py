def check_scoring(estimator=None, scoring=None, *, allow_none=False, raise_exc=True):
    """Determine scorer from user options.

    A TypeError will be thrown if the estimator cannot be scored.

    Parameters
    ----------
    estimator : estimator object implementing 'fit' or None, default=None
        The object to use to fit the data. If `None`, then this function may error
        depending on `allow_none`.

    scoring : str, callable, list, tuple, set, or dict, default=None
        Scorer to use. If `scoring` represents a single score, one can use:

        - a single string (see :ref:`scoring_string_names`);
        - a callable (see :ref:`scoring_callable`) that returns a single value;
        - `None`, the `estimator`'s
          :ref:`default evaluation criterion <scoring_api_overview>` is used.

        If `scoring` represents multiple scores, one can use:

        - a list, tuple or set of unique strings;
        - a callable returning a dictionary where the keys are the metric names and the
          values are the metric scorers;
        - a dictionary with metric names as keys and callables a values. The callables
          need to have the signature `callable(estimator, X, y)`.

    allow_none : bool, default=False
        Whether to return None or raise an error if no `scoring` is specified and the
        estimator has no `score` method.

    raise_exc : bool, default=True
        Whether to raise an exception (if a subset of the scorers in multimetric scoring
        fails) or to return an error code.

        - If set to `True`, raises the failing scorer's exception.
        - If set to `False`, a formatted string of the exception details is passed as
          result of the failing scorer(s).

        This applies if `scoring` is list, tuple, set, or dict. Ignored if `scoring` is
        a str or a callable.

        .. versionadded:: 1.6

    Returns
    -------
    scoring : callable
        A scorer callable object / function with signature ``scorer(estimator, X, y)``.

    Examples
    --------
    >>> from sklearn.datasets import load_iris
    >>> from sklearn.metrics import check_scoring
    >>> from sklearn.tree import DecisionTreeClassifier
    >>> X, y = load_iris(return_X_y=True)
    >>> classifier = DecisionTreeClassifier(max_depth=2).fit(X, y)
    >>> scorer = check_scoring(classifier, scoring='accuracy')
    >>> scorer(classifier, X, y)
    0.96...

    >>> from sklearn.metrics import make_scorer, accuracy_score, mean_squared_log_error
    >>> X, y = load_iris(return_X_y=True)
    >>> y *= -1
    >>> clf = DecisionTreeClassifier().fit(X, y)
    >>> scoring = {
    ...     "accuracy": make_scorer(accuracy_score),
    ...     "mean_squared_log_error": make_scorer(mean_squared_log_error),
    ... }
    >>> scoring_call = check_scoring(estimator=clf, scoring=scoring, raise_exc=False)
    >>> scores = scoring_call(clf, X, y)
    >>> scores
    {'accuracy': 1.0, 'mean_squared_log_error': 'Traceback ...'}
    """
    if isinstance(scoring, str):
        return get_scorer(scoring)
    if callable(scoring):
        # Heuristic to ensure user has not passed a metric
        module = getattr(scoring, "__module__", None)
        if (
            hasattr(module, "startswith")
            and module.startswith("sklearn.metrics.")
            and not module.startswith("sklearn.metrics._scorer")
            and not module.startswith("sklearn.metrics.tests.")
        ):
            raise ValueError(
                "scoring value %r looks like it is a metric "
                "function rather than a scorer. A scorer should "
                "require an estimator as its first parameter. "
                "Please use `make_scorer` to convert a metric "
                "to a scorer." % scoring
            )
        return get_scorer(scoring)
    if isinstance(scoring, (list, tuple, set, dict)):
        scorers = _check_multimetric_scoring(estimator, scoring=scoring)
        return _MultimetricScorer(scorers=scorers, raise_exc=raise_exc)
    if scoring is None:
        if hasattr(estimator, "score"):
            return _PassthroughScorer(estimator)
        elif allow_none:
            return None
        else:
            raise TypeError(
                "If no scoring is specified, the estimator passed should "
                "have a 'score' method. The estimator %r does not." % estimator
            )