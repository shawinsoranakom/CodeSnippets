def prefixed(*args):
            args = (kwargs["prefix"],) + args
            return "-".join(args)