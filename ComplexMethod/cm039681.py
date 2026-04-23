def _yield_masked_array_for_each_param(candidate_params):
    """
    Yield a masked array for each candidate param.

    `candidate_params` is a sequence of params which were used in
    a `GridSearchCV`. We use masked arrays for the results, as not
    all params are necessarily present in each element of
    `candidate_params`. For example, if using `GridSearchCV` with
    a `SVC` model, then one might search over params like:

        - kernel=["rbf"], gamma=[0.1, 1]
        - kernel=["poly"], degree=[1, 2]

    and then param `'gamma'` would not be present in entries of
    `candidate_params` corresponding to `kernel='poly'`.
    """
    n_candidates = len(candidate_params)
    param_results = defaultdict(dict)

    for cand_idx, params in enumerate(candidate_params):
        for name, value in params.items():
            param_results["param_%s" % name][cand_idx] = value

    for key, param_result in param_results.items():
        param_list = list(param_result.values())
        try:
            arr = np.array(param_list)
        except ValueError:
            # This can happen when param_list contains lists of different
            # lengths, for example:
            # param_list=[[1], [2, 3]]
            arr_dtype = np.dtype(object)
        else:
            # There are two cases when we don't use the automatically inferred
            # dtype when creating the array and we use object instead:
            # - string dtype
            # - when array.ndim > 1, that means that param_list was something
            #   like a list of same-size sequences, which gets turned into a
            #   multi-dimensional array but we want a 1d array
            arr_dtype = arr.dtype if arr.dtype.kind != "U" and arr.ndim == 1 else object

        # Use one MaskedArray and mask all the places where the param is not
        # applicable for that candidate (which may not contain all the params).
        ma = MaskedArray(np.empty(n_candidates, dtype=arr_dtype), mask=True)
        for index, value in param_result.items():
            # Setting the value at an index unmasks that index
            ma[index] = value
        yield (key, ma)