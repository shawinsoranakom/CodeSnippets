def test_extending_entity_description(snapshot: SnapshotAssertion) -> None:
    """Test extending entity descriptions."""

    @dataclasses.dataclass(frozen=True)
    class FrozenEntityDescription(entity.EntityDescription):
        extra: str = None

    obj = FrozenEntityDescription("blah", extra="foo", name="name")
    assert obj == snapshot
    assert obj == FrozenEntityDescription("blah", extra="foo", name="name")
    assert repr(obj) == snapshot

    # Try mutating
    with pytest.raises(dataclasses.FrozenInstanceError):
        obj.name = "mutate"
    with pytest.raises(dataclasses.FrozenInstanceError):
        delattr(obj, "name")

    @dataclasses.dataclass
    class ThawedEntityDescription(entity.EntityDescription):
        extra: str = None

    obj = ThawedEntityDescription("blah", extra="foo", name="name")
    assert obj == snapshot
    assert obj == ThawedEntityDescription("blah", extra="foo", name="name")
    assert repr(obj) == snapshot

    # Try mutating
    obj.name = "mutate"
    assert obj.name == "mutate"
    delattr(obj, "key")
    assert not hasattr(obj, "key")

    # Try multiple levels of FrozenOrThawed
    class ExtendedEntityDescription(entity.EntityDescription, frozen_or_thawed=True):
        extension: str = None

    @dataclasses.dataclass(frozen=True)
    class MyExtendedEntityDescription(ExtendedEntityDescription):
        extra: str = None

    obj = MyExtendedEntityDescription("blah", extension="ext", extra="foo", name="name")
    assert obj == snapshot
    assert obj == MyExtendedEntityDescription(
        "blah", extension="ext", extra="foo", name="name"
    )
    assert repr(obj) == snapshot

    # Try multiple direct parents
    @dataclasses.dataclass(frozen=True)
    class MyMixin1:
        mixin: str

    @dataclasses.dataclass
    class MyMixin2:
        mixin: str

    @dataclasses.dataclass(frozen=True)
    class MyMixin3:
        mixin: str = None

    @dataclasses.dataclass
    class MyMixin4:
        mixin: str = None

    @dataclasses.dataclass(frozen=True, kw_only=True)
    class ComplexEntityDescription1A(MyMixin1, entity.EntityDescription):
        extra: str = None

    obj = ComplexEntityDescription1A(
        key="blah", extra="foo", mixin="mixin", name="name"
    )
    assert obj == snapshot
    assert obj == ComplexEntityDescription1A(
        key="blah", extra="foo", mixin="mixin", name="name"
    )
    assert repr(obj) == snapshot

    @dataclasses.dataclass(frozen=True, kw_only=True)
    class ComplexEntityDescription1B(entity.EntityDescription, MyMixin1):
        extra: str = None

    obj = ComplexEntityDescription1B(
        key="blah", extra="foo", mixin="mixin", name="name"
    )
    assert obj == snapshot
    assert obj == ComplexEntityDescription1B(
        key="blah", extra="foo", mixin="mixin", name="name"
    )
    assert repr(obj) == snapshot

    @dataclasses.dataclass(frozen=True)
    class ComplexEntityDescription1C(MyMixin1, entity.EntityDescription):
        extra: str = None

    obj = ComplexEntityDescription1C(
        key="blah", extra="foo", mixin="mixin", name="name"
    )
    assert obj == snapshot
    assert obj == ComplexEntityDescription1C(
        key="blah", extra="foo", mixin="mixin", name="name"
    )
    assert repr(obj) == snapshot

    @dataclasses.dataclass(frozen=True)
    class ComplexEntityDescription1D(entity.EntityDescription, MyMixin1):
        extra: str = None

    obj = ComplexEntityDescription1D(
        key="blah", extra="foo", mixin="mixin", name="name"
    )
    assert obj == snapshot
    assert obj == ComplexEntityDescription1D(
        key="blah", extra="foo", mixin="mixin", name="name"
    )
    assert repr(obj) == snapshot

    @dataclasses.dataclass(kw_only=True)
    class ComplexEntityDescription2A(MyMixin2, entity.EntityDescription):
        extra: str = None

    obj = ComplexEntityDescription2A(
        key="blah", extra="foo", mixin="mixin", name="name"
    )
    assert obj == snapshot
    assert obj == ComplexEntityDescription2A(
        key="blah", extra="foo", mixin="mixin", name="name"
    )
    assert repr(obj) == snapshot

    @dataclasses.dataclass(kw_only=True)
    class ComplexEntityDescription2B(entity.EntityDescription, MyMixin2):
        extra: str = None

    obj = ComplexEntityDescription2B(
        key="blah", extra="foo", mixin="mixin", name="name"
    )
    assert obj == snapshot
    assert obj == ComplexEntityDescription2B(
        key="blah", extra="foo", mixin="mixin", name="name"
    )
    assert repr(obj) == snapshot

    @dataclasses.dataclass
    class ComplexEntityDescription2C(MyMixin2, entity.EntityDescription):
        extra: str = None

    obj = ComplexEntityDescription2C(
        key="blah", extra="foo", mixin="mixin", name="name"
    )
    assert obj == snapshot
    assert obj == ComplexEntityDescription2C(
        key="blah", extra="foo", mixin="mixin", name="name"
    )
    assert repr(obj) == snapshot

    @dataclasses.dataclass
    class ComplexEntityDescription2D(entity.EntityDescription, MyMixin2):
        extra: str = None

    obj = ComplexEntityDescription2D(
        key="blah", extra="foo", mixin="mixin", name="name"
    )
    assert obj == snapshot
    assert obj == ComplexEntityDescription2D(
        key="blah", extra="foo", mixin="mixin", name="name"
    )
    assert repr(obj) == snapshot

    @dataclasses.dataclass(frozen=True, kw_only=True)
    class ComplexEntityDescription3A(MyMixin3, entity.EntityDescription):
        extra: str = None

    obj = ComplexEntityDescription3A(
        key="blah", extra="foo", mixin="mixin", name="name"
    )
    assert obj == snapshot
    assert obj == ComplexEntityDescription3A(
        key="blah", extra="foo", mixin="mixin", name="name"
    )
    assert repr(obj) == snapshot

    @dataclasses.dataclass(frozen=True, kw_only=True)
    class ComplexEntityDescription3B(entity.EntityDescription, MyMixin3):
        extra: str = None

    obj = ComplexEntityDescription3B(
        key="blah", extra="foo", mixin="mixin", name="name"
    )
    assert obj == snapshot
    assert obj == ComplexEntityDescription3B(
        key="blah", extra="foo", mixin="mixin", name="name"
    )
    assert repr(obj) == snapshot

    with pytest.raises(TypeError):

        @dataclasses.dataclass(frozen=True)
        class ComplexEntityDescription3C(MyMixin3, entity.EntityDescription):
            extra: str = None

    with pytest.raises(TypeError):

        @dataclasses.dataclass(frozen=True)
        class ComplexEntityDescription3D(entity.EntityDescription, MyMixin3):
            extra: str = None

    @dataclasses.dataclass(kw_only=True)
    class ComplexEntityDescription4A(MyMixin4, entity.EntityDescription):
        extra: str = None

    obj = ComplexEntityDescription4A(
        key="blah", extra="foo", mixin="mixin", name="name"
    )
    assert obj == snapshot
    assert obj == ComplexEntityDescription4A(
        key="blah", extra="foo", mixin="mixin", name="name"
    )
    assert repr(obj) == snapshot

    @dataclasses.dataclass(kw_only=True)
    class ComplexEntityDescription4B(entity.EntityDescription, MyMixin4):
        extra: str = None

    obj = ComplexEntityDescription4B(
        key="blah", extra="foo", mixin="mixin", name="name"
    )
    assert obj == snapshot
    assert obj == ComplexEntityDescription4B(
        key="blah", extra="foo", mixin="mixin", name="name"
    )
    assert repr(obj) == snapshot

    with pytest.raises(TypeError):

        @dataclasses.dataclass
        class ComplexEntityDescription4C(MyMixin4, entity.EntityDescription):
            extra: str = None

    with pytest.raises(TypeError):

        @dataclasses.dataclass
        class ComplexEntityDescription4D(entity.EntityDescription, MyMixin4):
            extra: str = None

    # Try inheriting with custom init
    @dataclasses.dataclass
    class CustomInitEntityDescription(entity.EntityDescription):
        def __init__(self, extra, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self.extra: str = extra

    obj = CustomInitEntityDescription(key="blah", extra="foo", name="name")
    assert obj == snapshot
    assert obj == CustomInitEntityDescription(key="blah", extra="foo", name="name")
    assert repr(obj) == snapshot