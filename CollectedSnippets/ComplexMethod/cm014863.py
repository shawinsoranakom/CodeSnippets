def generate_tensor_like_torch_implementations():
    untested_funcs = []
    testing_overrides = get_testing_overrides()
    # test/test_cpp_api_parity.py monkeypatches torch.nn to have a new
    # function sample_functional.  Depending on what order you run pytest
    # collection, this may trigger the error here.  This is a hack to fix
    # the problem.  A more proper fix is to make the "not tested" check
    # a test on its own, and to make sure the monkeypatch is only installed
    # for the span of the relevant test (and deleted afterwards)
    testing_ignore = {"sample_functional", "autocast"}
    for namespace, funcs in get_overridable_functions().items():
        for func in funcs:
            if func not in testing_overrides and func.__name__ not in testing_ignore:
                untested_funcs.append(f"{namespace}.{func.__name__}")
    msg = (
        "The following functions are not tested for __torch_function__ "
        "support, please ensure there is an entry in the dict returned by "
        "torch.overrides.get_testing_overrides for this function or if a "
        "__torch_function__ override does not make sense, add an entry to "
        "the tuple returned by torch._overrides.get_ignored_functions.\n\n{}"
    )
    if len(untested_funcs) != 0:
        raise AssertionError(msg.format(pprint.pformat(untested_funcs)))
    for func, override in testing_overrides.items():
        # decorate the overrides with implements_tensor_like if it's not a
        # torch.Tensor method
        wrapped = triggered_wrapper(override)
        # See note: "_triggered wrapper"
        WRAPPED_TRIGGERED_IMPLS[func] = wrapped
        if is_tensor_method_or_property(func):
            implements_sub(func)(wrapped)
        else:
            implements_tensor_like(func)(wrapped)