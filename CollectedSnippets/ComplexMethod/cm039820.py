def assert_docstring_consistency(
    objects,
    include_params=False,
    exclude_params=None,
    include_attrs=False,
    exclude_attrs=None,
    include_returns=False,
    exclude_returns=None,
    descr_regex_pattern=None,
    ignore_types=tuple(),
):
    r"""Check consistency between docstring parameters/attributes/returns of objects.

    Checks if parameters/attributes/returns have the same type specification and
    description (ignoring whitespace) across `objects`. Intended to be used for
    related classes/functions/data descriptors.

    Entries that do not appear across all `objects` are ignored.

    Parameters
    ----------
    objects : list of {classes, functions, data descriptors}
        Objects to check.
        Objects may be classes, functions or data descriptors with docstrings that
        can be parsed by numpydoc.

    include_params : list of str or bool, default=False
        List of parameters to be included. If True, all parameters are included,
        if False, checking is skipped for parameters.
        Can only be set if `exclude_params` is None.

    exclude_params : list of str or None, default=None
        List of parameters to be excluded. If None, no parameters are excluded.
        Can only be set if `include_params` is True.

    include_attrs : list of str or bool, default=False
        List of attributes to be included. If True, all attributes are included,
        if False, checking is skipped for attributes.
        Can only be set if `exclude_attrs` is None.

    exclude_attrs : list of str or None, default=None
        List of attributes to be excluded. If None, no attributes are excluded.
        Can only be set if `include_attrs` is True.

    include_returns : list of str or bool, default=False
        List of returns to be included. If True, all returns are included,
        if False, checking is skipped for returns.
        Can only be set if `exclude_returns` is None.

    exclude_returns : list of str or None, default=None
        List of returns to be excluded. If None, no returns are excluded.
        Can only be set if `include_returns` is True.

    descr_regex_pattern : str, default=None
        Regular expression to match to all descriptions of included
        parameters/attributes/returns. If None, will revert to default behavior
        of comparing descriptions between objects.

    ignore_types : tuple of str, default=tuple()
        Tuple of parameter/attribute/return names to exclude from type description
        matching between objects.

    Examples
    --------
    >>> from sklearn.metrics import (accuracy_score, classification_report,
    ... mean_absolute_error, mean_squared_error, median_absolute_error)
    >>> from sklearn.utils._testing import assert_docstring_consistency
    ... # doctest: +SKIP
    >>> assert_docstring_consistency([mean_absolute_error, mean_squared_error],
    ... include_params=['y_true', 'y_pred', 'sample_weight'])  # doctest: +SKIP
    >>> assert_docstring_consistency([median_absolute_error, mean_squared_error],
    ... include_params=True)  # doctest: +SKIP
    >>> assert_docstring_consistency([accuracy_score, classification_report],
    ... include_params=["y_true"],
    ... descr_regex_pattern=r"Ground truth \(correct\) (labels|target values)")
    ... # doctest: +SKIP
    """
    from numpydoc.docscrape import NumpyDocString

    Args = namedtuple("args", ["include", "exclude", "arg_name"])

    def _create_args(include, exclude, arg_name, section_name):
        if exclude and include is not True:
            raise TypeError(
                f"The 'exclude_{arg_name}' argument can be set only when the "
                f"'include_{arg_name}' argument is True."
            )
        if include is False:
            return {}
        return {section_name: Args(include, exclude, arg_name)}

    section_args = {
        **_create_args(include_params, exclude_params, "params", "Parameters"),
        **_create_args(include_attrs, exclude_attrs, "attrs", "Attributes"),
        **_create_args(include_returns, exclude_returns, "returns", "Returns"),
    }

    objects_doc = dict()
    for obj in objects:
        if (
            inspect.isdatadescriptor(obj)
            or inspect.isfunction(obj)
            or inspect.isclass(obj)
        ):
            objects_doc[obj.__name__] = NumpyDocString(inspect.getdoc(obj))
        else:
            raise TypeError(
                "All 'objects' must be one of: function, class or descriptor, "
                f"got a: {type(obj)}."
            )

    n_objects = len(objects)
    for section, args in section_args.items():
        type_items = defaultdict(lambda: defaultdict(list))
        desc_items = defaultdict(lambda: defaultdict(list))
        for obj_name, obj_doc in objects_doc.items():
            for item_name, type_def, desc in obj_doc[section]:
                if _check_item_included(item_name, args):
                    # Normalize white space
                    type_def = " ".join(type_def.strip().split())
                    desc = " ".join(chain.from_iterable(line.split() for line in desc))
                    # Use string type/desc as key, to group consistent objs together
                    type_items[item_name][type_def].append(obj_name)
                    desc_items[item_name][desc].append(obj_name)

        _check_consistency_items(
            type_items,
            "type specification",
            section,
            n_objects,
            ignore_types=ignore_types,
        )
        _check_consistency_items(
            desc_items,
            "description",
            section,
            n_objects,
            descr_regex_pattern=descr_regex_pattern,
        )