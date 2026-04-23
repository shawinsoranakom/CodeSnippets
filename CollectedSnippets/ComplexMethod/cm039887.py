def compute_class_weight(class_weight, *, classes, y, sample_weight=None):
    """Estimate class weights for unbalanced datasets.

    Parameters
    ----------
    class_weight : dict, "balanced" or None
        If "balanced", class weights will be given by
        `n_samples / (n_classes * np.bincount(y))` or their weighted equivalent if
        `sample_weight` is provided.
        If a dictionary is given, keys are classes and values are corresponding class
        weights.
        If `None` is given, the class weights will be uniform.

    classes : ndarray
        Array of the classes occurring in the data, as given by
        `np.unique(y_org)` with `y_org` the original class labels.

    y : array-like of shape (n_samples,)
        Array of original class labels per sample.

    sample_weight : array-like of shape (n_samples,), default=None
        Array of weights that are assigned to individual samples. Only used when
        `class_weight='balanced'`.

    Returns
    -------
    class_weight_vect : ndarray of shape (n_classes,)
        Array with `class_weight_vect[i]` the weight for i-th class.

    References
    ----------
    The "balanced" heuristic is inspired by
    Logistic Regression in Rare Events Data, King, Zen, 2001.

    Examples
    --------
    >>> import numpy as np
    >>> from sklearn.utils.class_weight import compute_class_weight
    >>> y = [1, 1, 1, 1, 0, 0]
    >>> compute_class_weight(class_weight="balanced", classes=np.unique(y), y=y)
    array([1.5 , 0.75])
    """
    # Import error caused by circular imports.
    from sklearn.preprocessing import LabelEncoder

    xp, _, device_ = get_namespace_and_device(y, classes)
    unique_y = xp.unique_values(y)
    if set(move_to(unique_y, xp=np, device="cpu")) - set(
        move_to(classes, xp=np, device="cpu")
    ):
        raise ValueError("classes should include all valid labels that can be in y")
    if class_weight is None or len(class_weight) == 0:
        # uniform class weights
        weight = xp.ones(classes.shape[0], device=device_)
    elif class_weight == "balanced":
        # Find the weight of each class as present in y.
        le = LabelEncoder()
        y_ind = le.fit_transform(y)
        if not all(_isin(classes, xp.astype(le.classes_, classes.dtype), xp=xp)):
            raise ValueError("classes should have valid labels that are in y")

        if _is_numpy_namespace(xp) and sample_weight is not None:
            sample_weight = move_to(sample_weight, xp=np, device="cpu")

        sample_weight = _check_sample_weight(sample_weight, y)
        weighted_class_counts = _bincount(y_ind, weights=sample_weight, xp=xp)
        recip_freq = xp.sum(weighted_class_counts) / (
            size(le.classes_) * weighted_class_counts
        )
        weight = recip_freq[le.transform(classes)]
    else:
        # user-defined dictionary
        weight = xp.ones(size(classes), device=device_)
        unweighted_classes = []
        for i, c in enumerate(classes):
            try:
                c = int(c)
            except ValueError:  # `classes` contains strings
                c = str(c)
            if c in class_weight:
                weight[i] = class_weight[c]
            else:
                unweighted_classes.append(c)

        n_weighted_classes = size(classes) - len(unweighted_classes)
        if unweighted_classes and n_weighted_classes != len(class_weight):
            unweighted_classes_user_friendly_str = np.array(unweighted_classes).tolist()
            raise ValueError(
                f"The classes, {unweighted_classes_user_friendly_str}, are not in"
                " class_weight"
            )

    return weight