def parse_kv(args, check_raw=False):
    """
    Convert a string of key/value items to a dict. If any free-form params
    are found and the check_raw option is set to True, they will be added
    to a new parameter called '_raw_params'. If check_raw is not enabled,
    they will simply be ignored.
    """

    tags = []
    if origin_tag := Origin.get_tag(args):
        # NB: adjusting the column number is left as an exercise for the reader
        tags.append(origin_tag)
    if trusted_tag := TrustedAsTemplate.get_tag(args):
        tags.append(trusted_tag)

    args = to_text(args, nonstring='passthru')

    options = {}
    if args is not None:
        vargs = split_args(args)

        raw_params = []
        for orig_x in vargs:
            x = _decode_escapes(orig_x)
            if "=" in x:
                pos = 0
                try:
                    while True:
                        pos = x.index('=', pos + 1)
                        if pos > 0 and x[pos - 1] != '\\':
                            break
                except ValueError:
                    # ran out of string, but we must have some escaped equals,
                    # so replace those and append this to the list of raw params
                    raw_params.append(x.replace('\\=', '='))
                    continue

                k = x[:pos]
                v = x[pos + 1:]

                # FIXME: make the retrieval of this list of shell/command options a function, so the list is centralized
                if check_raw and k not in ('creates', 'removes', 'chdir', 'executable', 'warn', 'stdin', 'stdin_add_newline', 'strip_empty_ends'):
                    raw_params.append(orig_x)
                else:
                    options[k.strip()] = unquote(v.strip())
            else:
                raw_params.append(orig_x)

        # recombine the free-form params, if any were found, and assign
        # them to a special option for use later by the shell/command module
        if len(raw_params) > 0:
            options[u'_raw_params'] = join_args(raw_params)

    if tags:
        options = {AnsibleTagHelper.tag(k, tags): AnsibleTagHelper.tag(v, tags) for k, v in options.items()}

    if origin_tag:
        options = origin_tag.tag(options)

    return options