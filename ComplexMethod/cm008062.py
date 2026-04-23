def _dict_from_options_callback(
            option, opt_str, value, parser,
            allowed_keys=r'[\w-]+', delimiter=':', default_key=None, process=None, multiple_keys=True,
            process_key=str.lower, append=False):

        out_dict = dict(getattr(parser.values, option.dest))
        multiple_args = not isinstance(value, str)
        if multiple_keys:
            allowed_keys = fr'({allowed_keys})(,({allowed_keys}))*'
        mobj = re.match(
            fr'(?is)(?P<keys>{allowed_keys}){delimiter}(?P<val>.*)$',
            value[0] if multiple_args else value)
        if mobj is not None:
            keys, val = mobj.group('keys').split(','), mobj.group('val')
            if multiple_args:
                val = [val, *value[1:]]
        elif default_key is not None:
            keys, val = variadic(default_key), value
        else:
            raise optparse.OptionValueError(
                f'wrong {opt_str} formatting; it should be {option.metavar}, not "{value}"')
        try:
            keys = map(process_key, keys) if process_key else keys
            val = process(val) if process else val
        except Exception as err:
            raise optparse.OptionValueError(f'wrong {opt_str} formatting; {err}')
        for key in keys:
            out_dict[key] = [*out_dict.get(key, []), val] if append else val
        setattr(parser.values, option.dest, out_dict)