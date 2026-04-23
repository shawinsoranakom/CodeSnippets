def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not cls.screenshots:
            return

        for name, func in list(cls.__dict__.items()):
            if not hasattr(func, "_screenshot_cases"):
                continue
            # Remove the main test.
            delattr(cls, name)
            # Add separate tests for each screenshot type.
            for screenshot_case in getattr(func, "_screenshot_cases"):

                @wraps(func)
                def test(self, *args, _func=func, _case=screenshot_case, **kwargs):
                    with getattr(self, _case)():
                        return _func(self, *args, **kwargs)

                test.__name__ = f"{name}_{screenshot_case}"
                test.__qualname__ = f"{test.__qualname__}_{screenshot_case}"
                test._screenshot_name = name
                test._screenshot_case = screenshot_case
                setattr(cls, test.__name__, test)