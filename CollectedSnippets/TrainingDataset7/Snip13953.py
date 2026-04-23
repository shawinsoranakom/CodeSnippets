def skip_wrapper(*args, **kwargs):
                if (
                    args
                    and isinstance(args[0], unittest.TestCase)
                    and connection.alias not in getattr(args[0], "databases", {})
                ):
                    raise ValueError(
                        "%s cannot be used on %s as %s doesn't allow queries "
                        "against the %r database."
                        % (
                            name,
                            args[0],
                            args[0].__class__.__qualname__,
                            connection.alias,
                        )
                    )
                if condition():
                    raise unittest.SkipTest(reason)
                return test_func(*args, **kwargs)