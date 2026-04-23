def check_estimator(
    estimator=None,
    *,
    legacy: bool = True,
    expected_failed_checks: dict[str, str] | None = None,
    on_skip: Literal["warn"] | None = "warn",
    on_fail: Literal["raise", "warn"] | None = "raise",
    callback: Callable | None = None,
):
    """Check if estimator adheres to scikit-learn conventions.

    This function will run an extensive test-suite for input validation,
    shapes, etc, making sure that the estimator complies with `scikit-learn`
    conventions as detailed in :ref:`rolling_your_own_estimator`.
    Additional tests for classifiers, regressors, clustering or transformers
    will be run if the Estimator class inherits from the corresponding mixin
    from sklearn.base.

    scikit-learn also provides a pytest specific decorator,
    :func:`~sklearn.utils.estimator_checks.parametrize_with_checks`, making it
    easier to test multiple estimators.

    Checks are categorised into the following groups:

    - API checks: a set of checks to ensure API compatibility with scikit-learn.
      Refer to https://scikit-learn.org/dev/developers/develop.html a requirement of
      scikit-learn estimators.
    - legacy: a set of checks which gradually will be grouped into other categories.

    Parameters
    ----------
    estimator : estimator object
        Estimator instance to check.

    legacy : bool, default=True
        Whether to include legacy checks. Over time we remove checks from this category
        and move them into their specific category.

        .. versionadded:: 1.6

    expected_failed_checks : dict, default=None
        A dictionary of the form::

            {
                "check_name": "this check is expected to fail because ...",
            }

        Where `"check_name"` is the name of the check, and `"my reason"` is why
        the check fails.

        .. versionadded:: 1.6

    on_skip : "warn", None, default="warn"
        This parameter controls what happens when a check is skipped.

        - "warn": A :class:`~sklearn.exceptions.SkipTestWarning` is logged
          and running tests continue.
        - None: No warning is logged and running tests continue.

        .. versionadded:: 1.6

    on_fail : {"raise", "warn"}, None, default="raise"
        This parameter controls what happens when a check fails.

        - "raise": The exception raised by the first failing check is raised and
          running tests are aborted. This does not included tests that are expected
          to fail.
        - "warn": A :class:`~sklearn.exceptions.EstimatorCheckFailedWarning` is logged
          and running tests continue.
        - None: No exception is raised and no warning is logged.

        Note that if ``on_fail != "raise"``, no exception is raised, even if the checks
        fail. You'd need to inspect the return result of ``check_estimator`` to check
        if any checks failed.

        .. versionadded:: 1.6

    callback : callable, or None, default=None
        This callback will be called with the estimator and the check name,
        the exception (if any), the status of the check (xfail, failed, skipped,
        passed), and the reason for the expected failure if the check is
        expected to fail. The callable's signature needs to be::

            def callback(
                estimator,
                check_name: str,
                exception: Exception,
                status: Literal["xfail", "failed", "skipped", "passed"],
                expected_to_fail: bool,
                expected_to_fail_reason: str,
            )

        ``callback`` cannot be provided together with ``on_fail="raise"``.

        .. versionadded:: 1.6

    Returns
    -------
    test_results : list
        List of dictionaries with the results of the failing tests, of the form::

            {
                "estimator": estimator,
                "check_name": check_name,
                "exception": exception,
                "status": status (one of "xfail", "failed", "skipped", "passed"),
                "expected_to_fail": expected_to_fail,
                "expected_to_fail_reason": expected_to_fail_reason,
            }

    Raises
    ------
    Exception
        If ``on_fail="raise"``, the exception raised by the first failing check is
        raised and running tests are aborted.

        Note that if ``on_fail != "raise"``, no exception is raised, even if the checks
        fail. You'd need to inspect the return result of ``check_estimator`` to check
        if any checks failed.

    See Also
    --------
    parametrize_with_checks : Pytest specific decorator for parametrizing estimator
        checks.
    estimator_checks_generator : Generator that yields (estimator, check) tuples.

    Examples
    --------
    >>> from sklearn.utils.estimator_checks import check_estimator
    >>> from sklearn.linear_model import LogisticRegression
    >>> check_estimator(LogisticRegression())
    [...]
    """
    if isinstance(estimator, type):
        msg = (
            "Passing a class was deprecated in version 0.23 "
            "and isn't supported anymore from 0.24."
            "Please pass an instance instead."
        )
        raise TypeError(msg)

    if on_fail == "raise" and callback is not None:
        raise ValueError("callback cannot be provided together with on_fail='raise'")

    name = type(estimator).__name__

    test_results = []

    for estimator, check in estimator_checks_generator(
        estimator,
        legacy=legacy,
        expected_failed_checks=expected_failed_checks,
        # Not marking tests to be skipped here, we run and simulate an xfail behavior
        mark=None,
    ):
        test_can_fail, reason = _should_be_skipped_or_marked(
            estimator, check, expected_failed_checks
        )
        try:
            check(estimator)
        except SkipTest as e:
            # We get here if the test raises SkipTest, which is expected in cases where
            # the check cannot run for instance if a required dependency is not
            # installed.
            check_result = {
                "estimator": estimator,
                "check_name": _check_name(check),
                "exception": e,
                "status": "skipped",
                "expected_to_fail": test_can_fail,
                "expected_to_fail_reason": reason,
            }
            if on_skip == "warn":
                warnings.warn(
                    f"Skipping check {_check_name(check)} for {name} because it raised "
                    f"{type(e).__name__}: {e}",
                    SkipTestWarning,
                )
        except Exception as e:
            if on_fail == "raise" and not test_can_fail:
                raise

            check_result = {
                "estimator": estimator,
                "check_name": _check_name(check),
                "exception": e,
                "expected_to_fail": test_can_fail,
                "expected_to_fail_reason": reason,
            }

            if test_can_fail:
                # This check failed, but could be expected to fail, therefore we mark it
                # as xfail.
                check_result["status"] = "xfail"
            else:
                check_result["status"] = "failed"

            if on_fail == "warn":
                warning = EstimatorCheckFailedWarning(**check_result)
                warnings.warn(warning)
        else:
            check_result = {
                "estimator": estimator,
                "check_name": _check_name(check),
                "exception": None,
                "status": "passed",
                "expected_to_fail": test_can_fail,
                "expected_to_fail_reason": reason,
            }

        test_results.append(check_result)

        if callback:
            callback(**check_result)

    return test_results