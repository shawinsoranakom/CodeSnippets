def test_repr_dict_class():
    class Foo:
        def __repr__(self):
            return util.repr_(self)

    foo = Foo()
    foo.bar = "bar"
    assert repr(foo) == "Foo(bar='bar')"