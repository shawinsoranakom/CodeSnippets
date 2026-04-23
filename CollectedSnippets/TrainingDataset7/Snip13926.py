def decorator(test_func):
        nonlocal condition
        if not (
            isinstance(test_func, type) and issubclass(test_func, unittest.TestCase)
        ):

            @wraps(test_func)
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

            test_item = skip_wrapper
        else:
            # Assume a class is decorated
            test_item = test_func
            databases = getattr(test_item, "databases", None)
            if not databases or connection.alias not in databases:
                # Defer raising to allow importing test class's module.
                def condition():
                    raise ValueError(
                        "%s cannot be used on %s as it doesn't allow queries "
                        "against the '%s' database."
                        % (
                            name,
                            test_item,
                            connection.alias,
                        )
                    )

            # Retrieve the possibly existing value from the class's dict to
            # avoid triggering the descriptor.
            skip = test_func.__dict__.get("__unittest_skip__")
            if isinstance(skip, CheckCondition):
                test_item.__unittest_skip__ = skip.add_condition(condition, reason)
            elif skip is not True:
                test_item.__unittest_skip__ = CheckCondition((condition, reason))
        return test_item