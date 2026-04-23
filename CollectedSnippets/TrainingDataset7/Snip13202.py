def args_check(name, func, provided):
        provided = list(provided)
        # First argument, filter input, is implied.
        plen = len(provided) + 1
        # Check to see if a decorator is providing the real function.
        func = inspect.unwrap(func)

        with lazy_annotations():
            args, _, _, defaults, _, _, _ = inspect.getfullargspec(func)
        alen = len(args)
        dlen = len(defaults or [])
        # Not enough OR Too many
        if plen < (alen - dlen) or plen > alen:
            raise TemplateSyntaxError(
                "%s requires %d arguments, %d provided" % (name, alen - dlen, plen)
            )

        return True