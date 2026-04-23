def mean_tweedie_deviance(y_true, y_pred, *, sample_weight=None, power=0):
    """Mean Tweedie deviance regression loss.

    Read more in the :ref:`User Guide <mean_tweedie_deviance>`.

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Ground truth (correct) target values.

    y_pred : array-like of shape (n_samples,)
        Estimated target values.

    sample_weight : array-like of shape (n_samples,), default=None
        Sample weights.

    power : float, default=0
        Tweedie power parameter. Either power <= 0 or power >= 1.

        The higher `p` the less weight is given to extreme
        deviations between true and predicted targets.

        - power < 0: Extreme stable distribution. Requires: y_pred > 0.
        - power = 0 : Normal distribution, output corresponds to
          mean_squared_error. y_true and y_pred can be any real numbers.
        - power = 1 : Poisson distribution. Requires: y_true >= 0 and
          y_pred > 0.
        - 1 < p < 2 : Compound Poisson distribution. Requires: y_true >= 0
          and y_pred > 0.
        - power = 2 : Gamma distribution. Requires: y_true > 0 and y_pred > 0.
        - power = 3 : Inverse Gaussian distribution. Requires: y_true > 0
          and y_pred > 0.
        - otherwise : Positive stable distribution. Requires: y_true > 0
          and y_pred > 0.

    Returns
    -------
    loss : float
        A non-negative floating point value (the best value is 0.0).

    Examples
    --------
    >>> from sklearn.metrics import mean_tweedie_deviance
    >>> y_true = [2, 0, 1, 4]
    >>> y_pred = [0.5, 0.5, 2., 2.]
    >>> mean_tweedie_deviance(y_true, y_pred, power=1)
    1.4260...
    """
    xp, _, device = get_namespace_and_device(y_pred)
    y_true, sample_weight = move_to(y_true, sample_weight, xp=xp, device=device)
    y_type, y_true, y_pred, sample_weight, _ = _check_reg_targets_with_floating_dtype(
        y_true, y_pred, sample_weight, multioutput=None, xp=xp
    )
    if y_type == "continuous-multioutput":
        raise ValueError("Multioutput not supported in mean_tweedie_deviance")

    if sample_weight is not None:
        sample_weight = column_or_1d(sample_weight)
        sample_weight = sample_weight[:, np.newaxis]

    message = f"Mean Tweedie deviance error with power={power} can only be used on "
    if power < 0:
        # 'Extreme stable', y any real number, y_pred > 0
        if xp.any(y_pred <= 0):
            raise ValueError(message + "strictly positive y_pred.")
    elif power == 0:
        # Normal, y and y_pred can be any real number
        pass
    elif 1 <= power < 2:
        # Poisson and compound Poisson distribution, y >= 0, y_pred > 0
        if xp.any(y_true < 0) or xp.any(y_pred <= 0):
            raise ValueError(message + "non-negative y and strictly positive y_pred.")
    elif power >= 2:
        # Gamma and Extreme stable distribution, y and y_pred > 0
        if xp.any(y_true <= 0) or xp.any(y_pred <= 0):
            raise ValueError(message + "strictly positive y and y_pred.")
    else:  # pragma: nocover
        # Unreachable statement
        raise ValueError

    return _mean_tweedie_deviance(
        y_true, y_pred, sample_weight=sample_weight, power=power
    )