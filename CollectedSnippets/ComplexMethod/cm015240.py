def make_test_cls_with_mocked_export(
    cls,
    cls_prefix,
    fn_suffix,
    mocked_export_fn,
    xfail_prop=None,
    test_only_if_no_xfail=False,
):
    MockedTestClass = type(f"{cls_prefix}{cls.__name__}", cls.__bases__, {})
    MockedTestClass.__qualname__ = MockedTestClass.__name__

    for name in dir(cls):
        if name.startswith("test_"):
            fn = getattr(cls, name)
            if not callable(fn):
                setattr(MockedTestClass, name, getattr(cls, name))
                continue
            new_name = f"{name}{fn_suffix}"
            new_fn = _make_fn_with_mocked_export(fn, mocked_export_fn)
            new_fn.__name__ = new_name
            if xfail_prop is not None and hasattr(fn, xfail_prop):
                new_fn = unittest.expectedFailure(new_fn)
            elif test_only_if_no_xfail and any(
                x.startswith("_expected_failure") for x in dir(fn)
            ):
                new_fn = unittest.skip(
                    "Will only be tested if no other tests are failing"
                )(new_fn)
            setattr(MockedTestClass, new_name, new_fn)
        # NB: Doesn't handle slots correctly, but whatever
        elif not hasattr(MockedTestClass, name):
            setattr(MockedTestClass, name, getattr(cls, name))

    return MockedTestClass