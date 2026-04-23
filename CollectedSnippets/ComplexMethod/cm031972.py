def add_checks_cli(parser, checks=None, *, add_flags=None):
    default = False
    if not checks:
        checks = list(CHECKS)
        default = True
    elif isinstance(checks, str):
        checks = [checks]
    if (add_flags is None and len(checks) > 1) or default:
        add_flags = True

    process_checks = add_sepval_cli(parser, '--check', 'checks', checks)
    if add_flags:
        for check in checks:
            parser.add_argument(f'--{check}', dest='checks',
                                action='append_const', const=check)
    return [
        process_checks,
    ]