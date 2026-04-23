def test_register_impl(self):
        assert "impl_a" in _custom_add.impls
        impl = _custom_add.impls["impl_a"]

        assert impl is impl_a
        assert impl.op is _custom_add
        assert impl.provider == "impl_a"
        assert callable(impl.impl_fn)

        # Test duplicate registration rejected
        with pytest.raises(AssertionError):

            @_custom_add.register_impl("impl_a")
            def impl_a_dup(x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
                return x + y + 30

        # Check the original impl is still intact
        assert _custom_add.impls["impl_a"] is impl_a

        # Check support all args
        assert impl_a.supports_all_args
        assert impl_b.supports_all_args
        assert not impl_even.supports_all_args