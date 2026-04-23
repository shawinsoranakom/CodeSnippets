def _get_inputs(
    form: FormElement,
    formdata: FormdataType,
    dont_click: bool,
    clickdata: dict[str, str | int] | None,
) -> list[FormdataKVType]:
    """Return a list of key-value pairs for the inputs found in the given form."""
    try:
        formdata_keys = dict(formdata or ()).keys()
    except (ValueError, TypeError):
        raise ValueError("formdata should be a dict or iterable of tuples") from None

    if not formdata:
        formdata = []
    inputs = form.xpath(
        "descendant::textarea"
        "|descendant::select"
        "|descendant::input[not(@type) or @type["
        ' not(re:test(., "^(?:submit|image|reset)$", "i"))'
        " and (../@checked or"
        '  not(re:test(., "^(?:checkbox|radio)$", "i")))]]',
        namespaces={"re": "http://exslt.org/regular-expressions"},
    )
    values: list[FormdataKVType] = [
        (k, "" if v is None else v)
        for k, v in (_value(e) for e in inputs)
        if k and k not in formdata_keys
    ]

    if not dont_click:
        clickable = _get_clickable(clickdata, form)
        if clickable and clickable[0] not in formdata and clickable[0] is not None:
            values.append(clickable)

    formdata_items = formdata.items() if isinstance(formdata, dict) else formdata
    values.extend((k, v) for k, v in formdata_items if v is not None)
    return values