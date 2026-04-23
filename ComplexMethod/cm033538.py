def test_slots(self, value: type) -> None:
        """Assert that __slots__ are properly defined on the given serializable type."""
        if value in (AnsibleSerializable, AnsibleTaggedObject):
            expect_slots = True  # non-dataclass base types have no attributes, but still use slots
        elif issubclass(value, (int, bytes, tuple, enum.Enum)):
            # non-empty slots are not supported by these variable-length data types
            # see: https://docs.python.org/3/reference/datamodel.html
            expect_slots = False
        elif issubclass(value, AnsibleSerializableDataclass) or value == AnsibleSerializableDataclass:
            assert dataclasses.is_dataclass(value)  # everything extending AnsibleSerializableDataclass must be a dataclass
            expect_slots = sys.version_info >= (3, 10)  # 3.10+ dataclasses have attributes (and support slots)
        else:
            expect_slots = True  # normal types have attributes (and slots)

        # check for slots on the type itself, ignoring slots on parents
        has_slots = '__slots__' in value.__dict__
        assert has_slots == expect_slots

        # instances of concrete types using __slots__ should not have __dict__ (which would indicate missing __slots__ definitions in the class hierarchy)
        serializable_instance = {type(instance): instance for instance in self.serializable_instances}.get(value)

        if serializable_instance:
            has_dict = hasattr(serializable_instance, '__dict__')
            assert has_dict != expect_slots