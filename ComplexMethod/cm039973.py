def _write_label_html(
    out,
    params,
    attrs,
    name,
    name_details,
    name_caption=None,
    doc_link_label=None,
    features=None,
    outer_class="sk-label-container",
    inner_class="sk-label",
    checked=False,
    doc_link="",
    is_fitted_css_class="",
    is_fitted_icon="",
    param_prefix="",
):
    """Write labeled html with or without a dropdown with named details.

    Parameters
    ----------
    out : file-like object
        The file to write the HTML representation to.
    params: str
        If estimator has `get_params` method, this is the HTML representation
        of the estimator's parameters and their values. When the estimator
        does not have `get_params`, it is an empty string.
    attrs: str
        If estimator is fitted, this is the HTML representation of its
        fitted attributes.
    name : str
        The label for the estimator. It corresponds either to the estimator class name
        for a simple estimator or in the case of a `Pipeline` and `ColumnTransformer`,
        it corresponds to the name of the step.
    name_details : str
        The details to show as content in the dropdown part of the toggleable label. It
        can contain information such as non-default parameters or column information for
        `ColumnTransformer`.
    name_caption : str, default=None
        The caption below the name. If `None`, no caption will be created.
    doc_link_label : str, default=None
        The label for the documentation link. If provided, the label would be
        "Documentation for {doc_link_label}". Otherwise it will look for `name`.
    outer_class : {"sk-label-container", "sk-item"}, default="sk-label-container"
        The CSS class for the outer container.
    inner_class : {"sk-label", "sk-estimator"}, default="sk-label"
        The CSS class for the inner container.
    checked : bool, default=False
        Whether the dropdown is folded or not. With a single estimator, we intend to
        unfold the content.
    doc_link : str, default=""
        The link to the documentation for the estimator. If an empty string, no link is
        added to the diagram. This can be generated for an estimator if it uses the
        `_HTMLDocumentationLinkMixin`.
    is_fitted_css_class : {"", "fitted"}
        The CSS class to indicate whether or not the estimator is fitted. The
        empty string means that the estimator is not fitted and "fitted" means that the
        estimator is fitted.
    is_fitted_icon : str, default=""
        The HTML representation to show the fitted information in the diagram. An empty
        string means that no information is shown.
    param_prefix : str, default=""
        The prefix to prepend to parameter names for nested estimators.
    """
    out.write(
        f'<div class="{outer_class}"><div'
        f' class="{inner_class} {is_fitted_css_class} sk-toggleable">'
    )
    name = html.escape(name)
    if name_details is not None:
        name_details = html.escape(str(name_details))
        checked_str = "checked" if checked else ""
        est_id = _ESTIMATOR_ID_COUNTER.get_id()

        if doc_link:
            doc_label = "<span>Online documentation</span>"
            if doc_link_label is not None:
                doc_label = f"<span>Documentation for {doc_link_label}</span>"
            elif name is not None:
                doc_label = f"<span>Documentation for {name}</span>"
            doc_link = (
                f'<a class="sk-estimator-doc-link {is_fitted_css_class}"'
                f' rel="noreferrer" target="_blank" href="{doc_link}">?{doc_label}</a>'
            )
        if name == "passthrough" or name_details == "[]":
            name_caption = ""
        name_caption_div = (
            ""
            if name_caption is None or name_caption == ""
            else f'<div class="caption">{html.escape(name_caption)}</div>'
        )
        name_caption_div = f"<div><div>{name}</div>{name_caption_div}</div>"
        links_div = (
            f"<div>{doc_link}{is_fitted_icon}</div>"
            if doc_link or is_fitted_icon
            else ""
        )
        label_arrow_class = (
            "" if name == "passthrough" else "sk-toggleable__label-arrow"
        )

        label_html = (
            f'<label for="{est_id}" class="sk-toggleable__label {is_fitted_css_class} '
            f'{label_arrow_class}">{name_caption_div}{links_div}</label>'
        )

        out.write(
            f'<input class="sk-toggleable__control sk-hidden--visually '
            f'sk-global" id="{est_id}" '
            f'type="checkbox" {checked_str}>{label_html}<div '
            f'class="sk-toggleable__content {is_fitted_css_class}" '
            f'data-param-prefix="{html.escape(param_prefix)}">'
        )

        out.write(params)
        out.write(attrs)
        if name_details and ("Pipeline" not in name) and not params:
            if name == "passthrough" or name_details == "[]":
                name_details = ""
            out.write(f"<pre>{name_details}</pre>")

        out.write("</div>")
        if features is None or len(features) == 0:
            features_div = ""
        else:
            features_div = _features_html(features, is_fitted_css_class)

        out.write("</div></div>")
        out.write(features_div)

    else:
        out.write(f"<label>{name}</label>")
        out.write("</div></div>")