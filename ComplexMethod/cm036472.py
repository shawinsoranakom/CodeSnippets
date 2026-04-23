def test_set_priority_scoped(self):
        assert _custom_add.get_priority() == []

        with _custom_add.set_priority(["impl_even", "impl_b"]):
            assert _custom_add.get_priority() == ["impl_even", "impl_b"]

            # Check nesting
            with _custom_add.set_priority(["impl_b"]):
                assert _custom_add.get_priority() == ["impl_b"]

            # Restored
            assert _custom_add.get_priority() == ["impl_even", "impl_b"]

            # Check that exception restores priority
            with pytest.raises(CustomError), _custom_add.set_priority(["impl_a"]):
                assert _custom_add.get_priority() == ["impl_a"]
                raise CustomError

            # Restored again
            assert _custom_add.get_priority() == ["impl_even", "impl_b"]

        # Restored to empty
        assert _custom_add.get_priority() == []