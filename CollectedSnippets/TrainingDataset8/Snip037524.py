def _unflatten_single_dict(flat_dict):
    """Convert a flat dict of key-value pairs to dict tree.

    Example
    -------

        _unflatten_single_dict({
          foo_bar_baz: 123,
          foo_bar_biz: 456,
          x_bonks: 'hi',
        })

        # Returns:
        # {
        #   foo: {
        #     bar: {
        #       baz: 123,
        #       biz: 456,
        #     },
        #   },
        #   x: {
        #     bonks: 'hi'
        #   }
        # }

    Parameters
    ----------
    flat_dict : dict
        A one-level dict where keys are fully-qualified paths separated by
        underscores.

    Returns
    -------
    dict
        A tree made of dicts inside of dicts.

    """
    out = dict()  # type: Dict[str, Any]
    for pathstr, v in flat_dict.items():
        path = pathstr.split("_")

        prev_dict = None  # type: Optional[Dict[str, Any]]
        curr_dict = out

        for k in path:
            if k not in curr_dict:
                curr_dict[k] = dict()
            prev_dict = curr_dict
            curr_dict = curr_dict[k]

        if prev_dict is not None:
            prev_dict[k] = v

    return out