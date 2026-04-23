def _write_estimator_html(
    out,
    estimator,
    estimator_label,
    estimator_label_details,
    is_fitted_css_class,
    is_fitted_icon="",
    first_call=False,
    param_prefix="",
):
    """Write estimator to html in serial, parallel, or by itself (single).

    For multiple estimators, this function is called recursively.

    Parameters
    ----------
    out : file-like object
        The file to write the HTML representation to.
    estimator : estimator object
        The estimator to visualize.
    estimator_label : str
        The label for the estimator. It corresponds either to the estimator class name
        for simple estimator or in the case of `Pipeline` and `ColumnTransformer`, it
        corresponds to the name of the step.
    estimator_label_details : str
        The details to show as content in the dropdown part of the toggleable label.
        It can contain information as non-default parameters or column information for
        `ColumnTransformer`.
    is_fitted_css_class : {"", "fitted"}
        The CSS class to indicate whether or not the estimator is fitted or not. The
        empty string means that the estimator is not fitted and "fitted" means that the
        estimator is fitted.
    is_fitted_icon : str, default=""
        The HTML representation to show the fitted information in the diagram. An empty
        string means that no information is shown. If the estimator to be shown is not
        the first estimator (i.e. `first_call=False`), `is_fitted_icon` is always an
        empty string.
    first_call : bool, default=False
        Whether this is the first time this function is called.
    param_prefix : str, default=""
        The prefix to prepend to parameter names for nested estimators.
        For example, in a pipeline this might be "pipeline__stepname__".
    """
    from sklearn.compose import ColumnTransformer

    if first_call:
        est_block = _get_visual_block(estimator)
    else:
        is_fitted_icon = ""
        with config_context(print_changed_only=True):
            est_block = _get_visual_block(estimator)
    # `estimator` can also be an instance of `_VisualBlock`
    if hasattr(estimator, "_get_doc_link"):
        doc_link = estimator._get_doc_link()
    else:
        doc_link = ""

    has_feature_names_out = hasattr(estimator, "get_feature_names_out")
    is_not_pipeline_step = not hasattr(estimator, "steps")

    if est_block.kind in ("serial", "parallel"):
        dashed_wrapped = first_call or est_block.dash_wrapped
        dash_cls = " sk-dashed-wrapped" if dashed_wrapped else ""
        out.write(f'<div class="sk-item{dash_cls}">')
        if estimator_label:
            if hasattr(estimator, "get_params") and hasattr(
                estimator, "_get_params_html"
            ):
                params = estimator._get_params_html(False, doc_link)._repr_html_inner()
            else:
                params = ""
            if (
                hasattr(estimator, "_get_fitted_attr_html")
                and is_fitted_css_class == "fitted"
            ):
                fitted_attrs = estimator._get_fitted_attr_html(doc_link)
                attrs = fitted_attrs._repr_html_inner() if len(fitted_attrs) > 0 else ""

            else:
                attrs = ""

            _write_label_html(
                out,
                params,
                attrs,
                estimator_label,
                estimator_label_details,
                doc_link=doc_link,
                features=None,
                is_fitted_css_class=is_fitted_css_class,
                is_fitted_icon=is_fitted_icon,
                param_prefix=param_prefix,
            )

        kind = est_block.kind
        out.write(f'<div class="sk-{kind}">')
        est_infos = zip(est_block.estimators, est_block.names, est_block.name_details)

        for est, name, name_details in est_infos:
            # Build the parameter prefix for nested estimators

            if param_prefix and hasattr(name, "split"):
                # If we already have a prefix, append the new component
                new_prefix = f"{param_prefix}{name.split(':')[0]}__"
            elif hasattr(name, "split"):
                # If this is the first level, start the prefix
                new_prefix = f"{name.split(':')[0]}__" if name else ""
            else:
                new_prefix = param_prefix

            if kind == "serial":
                _write_estimator_html(
                    out,
                    est,
                    name,
                    name_details,
                    is_fitted_css_class=is_fitted_css_class,
                    param_prefix=new_prefix,
                )
            else:  # parallel
                out.write('<div class="sk-parallel-item">')
                # wrap element in a serial visualblock
                serial_block = _VisualBlock("serial", [est], dash_wrapped=False)
                _write_estimator_html(
                    out,
                    serial_block,
                    name,
                    name_details,
                    is_fitted_css_class=is_fitted_css_class,
                    param_prefix=new_prefix,
                )
                out.write("</div>")  # sk-parallel-item

        out.write("</div>")

        is_column_transformer = isinstance(estimator, ColumnTransformer)
        has_single_estimator = len(est_block.estimators) == 1
        if (
            is_fitted_css_class
            and has_feature_names_out
            and is_not_pipeline_step
            and not (is_column_transformer and has_single_estimator)
        ):
            features_div = _features_html(
                estimator.get_feature_names_out(), is_fitted_css_class
            )
            total_output_features_item = (
                f"<div class='total_features'>{features_div}</div>"
            )
            out.write(total_output_features_item)

        out.write("</div>")
    elif est_block.kind == "single":
        if has_feature_names_out and is_not_pipeline_step and is_fitted_css_class:
            try:
                output_features = estimator.get_feature_names_out()
            except Exception:
                output_features = ""
        else:
            output_features = ""

        if est_block.names == "NoneType(...)":
            est_block.names = "passthrough"

        if (
            hasattr(estimator, "_get_params_html")
            and not est_block.names == "passthrough"
        ):
            params = estimator._get_params_html(doc_link=doc_link)._repr_html_inner()
        else:
            params = ""
        if (
            hasattr(estimator, "_get_fitted_attr_html")
            and not est_block.names == "passthrough"
            and is_fitted_css_class == "fitted"
        ):
            fitted_attrs = estimator._get_fitted_attr_html(doc_link)
            attrs = fitted_attrs._repr_html_inner() if len(fitted_attrs) > 0 else ""

        else:
            attrs = ""

        _write_label_html(
            out,
            params,
            attrs,
            est_block.names,
            est_block.name_details,
            est_block.name_caption,
            est_block.doc_link_label,
            outer_class="sk-item",
            inner_class="sk-estimator",
            checked=first_call,
            doc_link=doc_link,
            features=output_features,
            is_fitted_css_class=is_fitted_css_class,
            is_fitted_icon=is_fitted_icon,
            param_prefix=param_prefix,
        )