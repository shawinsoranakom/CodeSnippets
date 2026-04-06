def print_alias(known_args):
    settings.init(known_args)
    print(_get_alias(known_args))