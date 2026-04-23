def get_dunder_methods_to_intercept() -> list[str]:
    """
    Return a list of dunder methods on Jinja's StrictUndefined that should be overridden by Ansible's Marker.
    When new methods are added in future Python/Jinja versions, they need to be added to Marker or the ignore_names list below.
    """
    dunder_names = set(name for name in dir(jinja2.StrictUndefined) if name.startswith('__') and name.endswith('__'))

    strict_undefined_intercepted_method_names = set(
        name for name in dir(jinja2.StrictUndefined)
        if getattr(jinja2.StrictUndefined, name) is jinja2.StrictUndefined._fail_with_undefined_error and name != '_fail_with_undefined_error'
    )

    # Some attributes/methods are necessary for core Python interactions and must not be intercepted, thus they are excluded from this test.
    ignore_names = {
        '__class__',
        '__dir__',
        '__doc__',
        '__firstlineno__',
        '__getattr__',  # tested separately since it is intercepted with a custom method
        '__getattribute__',
        '__getitem__',  # tested separately since it is intercepted with a custom method
        '__getstate__',
        '__init__',
        '__init_subclass__',
        '__module__',
        '__new__',
        '__reduce__',
        '__reduce_ex__',
        '__setattr__',  # tested separately since it is intercepted with a custom method
        '__slots__',  # tested separately since it's not a method
        '__sizeof__',
        '__static_attributes__',
        '__subclasshook__',
    }

    # Some methods not intercepted by Jinja's StrictUndefined should be intercepted by Marker.
    additional_method_names = {
        '__aiter__',
        '__delattr__',
        '__format__',
        '__repr__',
        '__setitem__',
    }

    assert not strict_undefined_intercepted_method_names - dunder_names  # ensure Jinja intercepted methods have not been overlooked
    assert not ignore_names & additional_method_names  # ensure no overap between ignore_names and additional_method_names

    return sorted(dunder_names - ignore_names | additional_method_names)