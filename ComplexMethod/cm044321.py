def test_register_accessor_registers_and_warns_on_override():
    class Dummy:
        accessors = set()

    def accessor_factory(obj):
        return SimpleNamespace(called_with=obj)

    # Register new accessor
    decorator = Extension.register_accessor("foo", Dummy)
    returned = decorator(accessor_factory)
    assert returned is accessor_factory  # decorator returns the original accessor
    assert hasattr(Dummy, "foo")
    assert "foo" in Dummy.accessors
    # descriptor instance is stored in the class __dict__; accessing via the
    # class returns the result of descriptor.__get__, so inspect __dict__
    assert isinstance(Dummy.__dict__["foo"], CachedAccessor)

    # If attribute already exists, registration should warn
    Dummy.existing = "I exist"  #  type: ignore
    with pytest.warns(UserWarning):
        Extension.register_accessor("existing", Dummy)(accessor_factory)

    # Clean up
    if "foo" in Dummy.accessors:
        Dummy.accessors.remove("foo")
    if hasattr(Dummy, "foo"):
        delattr(Dummy, "foo")
    if hasattr(Dummy, "existing"):
        delattr(Dummy, "existing")