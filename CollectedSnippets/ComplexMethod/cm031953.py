def add_commands_cli(parser, commands, *, commonspecs=COMMON_CLI, subset=None):
    arg_processors = {}
    if isinstance(subset, str):
        cmdname = subset
        try:
            _, argspecs, _ = commands[cmdname]
        except KeyError:
            raise ValueError(f'unsupported subset {subset!r}')
        parser.set_defaults(cmd=cmdname)
        arg_processors[cmdname] = _add_cmd_cli(parser, commonspecs, argspecs)
    else:
        if subset is None:
            cmdnames = subset = list(commands)
        elif not subset:
            raise NotImplementedError
        elif isinstance(subset, set):
            cmdnames = [k for k in commands if k in subset]
            subset = sorted(subset)
        else:
            cmdnames = [n for n in subset if n in commands]
        if len(cmdnames) < len(subset):
            bad = tuple(n for n in subset if n not in commands)
            raise ValueError(f'unsupported subset {bad}')

        common = argparse.ArgumentParser(add_help=False)
        common_processors = apply_cli_argspecs(common, commonspecs)
        subs = parser.add_subparsers(dest='cmd')
        for cmdname in cmdnames:
            description, argspecs, _ = commands[cmdname]
            sub = subs.add_parser(
                cmdname,
                description=description,
                parents=[common],
            )
            cmd_processors = _add_cmd_cli(sub, (), argspecs)
            arg_processors[cmdname] = common_processors + cmd_processors
    return arg_processors