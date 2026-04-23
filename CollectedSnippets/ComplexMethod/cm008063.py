def _create_alias(option, opt_str, value, parser):
        aliases, opts = value
        try:
            nargs = len({i if f == '' else f
                         for i, (_, f, _, _) in enumerate(Formatter.parse(opts)) if f is not None})
            opts.format(*map(str, range(nargs)))  # validate
        except Exception as err:
            raise optparse.OptionValueError(f'wrong {opt_str} OPTIONS formatting; {err}')
        if alias_group not in parser.option_groups:
            parser.add_option_group(alias_group)

        aliases = (x if x.startswith('-') else f'--{x}' for x in map(str.strip, aliases.split(',')))
        try:
            args = [f'ARG{i}' for i in range(nargs)]
            alias_group.add_option(
                *aliases, nargs=nargs, dest=parser.ALIAS_DEST, type='str' if nargs else None,
                metavar=' '.join(args), help=opts.format(*args), action='callback',
                callback=_alias_callback, callback_kwargs={'opts': opts, 'nargs': nargs})
        except Exception as err:
            raise optparse.OptionValueError(f'wrong {opt_str} formatting; {err}')