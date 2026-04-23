def set_config(
    assume_finite=None,
    working_memory=None,
    print_changed_only=None,
    display=None,
    pairwise_dist_chunk_size=None,
    enable_cython_pairwise_dist=None,
    array_api_dispatch=None,
    transform_output=None,
    enable_metadata_routing=None,
    skip_parameter_validation=None,
    sparse_interface=None,
):
    """Set global scikit-learn configuration.

    These settings control the behaviour of scikit-learn functions during a library
    usage session. Global configuration defaults (as described in the parameter list
    below) take effect when scikit-learn is imported.

    This function can be used to modify the global scikit-learn configuration at
    runtime. Passing `None` as an argument (the default) leaves the corresponding
    setting unchanged. This allows users to selectively update the global configuration
    values without affecting the others.

    .. versionadded:: 0.19

    Parameters
    ----------
    assume_finite : bool, default=None
        If True, validation for finiteness will be skipped,
        saving time, but leading to potential crashes. If
        False, validation for finiteness will be performed,
        avoiding error. Global default: False.

        .. versionadded:: 0.19

    working_memory : int, default=None
        If set, scikit-learn will attempt to limit the size of temporary arrays
        to this number of MiB (per job when parallelised), often saving both
        computation time and memory on expensive operations that can be
        performed in chunks. Global default: 1024.

        .. versionadded:: 0.20

    print_changed_only : bool, default=None
        If True, only the parameters that were set to non-default
        values will be printed when printing an estimator. For example,
        ``print(SVC())`` while True will only print 'SVC()' while the default
        behaviour would be to print 'SVC(C=1.0, cache_size=200, ...)' with
        all the non-changed parameters. Global default: True.

        .. versionadded:: 0.21
        .. versionchanged:: 0.23
           Global default configuration changed from False to True.

    display : {'text', 'diagram'}, default=None
        If 'diagram', estimators will be displayed as a diagram in a Jupyter
        lab or notebook context. If 'text', estimators will be displayed as
        text. Global default: 'diagram'.

        .. versionadded:: 0.23

    pairwise_dist_chunk_size : int, default=None
        The number of row vectors per chunk for the accelerated pairwise-
        distances reduction backend. Global default: 256 (suitable for most of
        modern laptops' caches and architectures).

        Intended for easier benchmarking and testing of scikit-learn internals.
        End users are not expected to benefit from customizing this configuration
        setting.

        .. versionadded:: 1.1

    enable_cython_pairwise_dist : bool, default=None
        Use the accelerated pairwise-distances reduction backend when
        possible. Global default: True.

        Intended for easier benchmarking and testing of scikit-learn internals.
        End users are not expected to benefit from customizing this configuration
        setting.

        .. versionadded:: 1.1

    array_api_dispatch : bool, default=None
        Use Array API dispatching when inputs follow the Array API standard.
        Global default: False.

        See the :ref:`User Guide <array_api>` for more details.

        .. versionadded:: 1.2

    transform_output : str, default=None
        Configure output of `transform` and `fit_transform`.

        See :ref:`sphx_glr_auto_examples_miscellaneous_plot_set_output.py`
        for an example on how to use the API.

        - `"default"`: Default output format of a transformer
        - `"pandas"`: DataFrame output
        - `"polars"`: Polars output
        - `None`: Transform configuration is unchanged

        Global default: "default".

        .. versionadded:: 1.2
        .. versionadded:: 1.4
            `"polars"` option was added.

    enable_metadata_routing : bool, default=None
        Enable metadata routing. By default this feature is disabled.

        Refer to :ref:`metadata routing user guide <metadata_routing>` for more
        details.

        - `True`: Metadata routing is enabled
        - `False`: Metadata routing is disabled, use the old syntax.
        - `None`: Configuration is unchanged

        Global default: False.

        .. versionadded:: 1.3

    skip_parameter_validation : bool, default=None
        If `True`, disable the validation of the hyper-parameters' types and values in
        the fit method of estimators and for arguments passed to public helper
        functions. It can save time in some situations but can lead to low level
        crashes and exceptions with confusing error messages.
        Global default: False.

        Note that for data parameters, such as `X` and `y`, only type validation is
        skipped but validation with `check_array` will continue to run.

        .. versionadded:: 1.3

    sparse_interface : str, default="spmatrix"

        The sparse interface used for every sparse object that scikit-learn produces,
        e.g., function returns, estimator attributes, estimator properties, etc.

        - `"sparray"`: Return sparse as SciPy sparse array
        - `"spmatrix"`: Return sparse as SciPy sparse matrix

        .. versionadded:: 1.9

    See Also
    --------
    config_context : Context manager for global scikit-learn configuration.
    get_config : Retrieve current values of the global configuration.

    Examples
    --------
    >>> from sklearn import set_config
    >>> set_config(display='diagram')  # doctest: +SKIP
    """
    local_config = _get_threadlocal_config()

    if assume_finite is not None:
        local_config["assume_finite"] = assume_finite
    if working_memory is not None:
        local_config["working_memory"] = working_memory
    if print_changed_only is not None:
        local_config["print_changed_only"] = print_changed_only
    if display is not None:
        local_config["display"] = display
    if pairwise_dist_chunk_size is not None:
        local_config["pairwise_dist_chunk_size"] = pairwise_dist_chunk_size
    if enable_cython_pairwise_dist is not None:
        local_config["enable_cython_pairwise_dist"] = enable_cython_pairwise_dist
    if array_api_dispatch is not None:
        from sklearn.utils._array_api import _check_array_api_dispatch

        _check_array_api_dispatch(array_api_dispatch)
        local_config["array_api_dispatch"] = array_api_dispatch
    if transform_output is not None:
        local_config["transform_output"] = transform_output
    if enable_metadata_routing is not None:
        local_config["enable_metadata_routing"] = enable_metadata_routing
    if skip_parameter_validation is not None:
        local_config["skip_parameter_validation"] = skip_parameter_validation
    if sparse_interface is not None:
        local_config["sparse_interface"] = sparse_interface