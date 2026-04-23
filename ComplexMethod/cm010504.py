def go(m1: MetaTensorDesc[Any], m2: torch.Tensor) -> None:
        assert_eq(m1.dtype, m2.dtype)
        if not skip_symbolic:
            assert_eq(m1.shape, m2.shape)
        assert_eq(m1.requires_grad, m2.requires_grad)
        if not skip_leaf:
            assert_eq(m1.is_leaf, m2.is_leaf)
        # MetaTensorDesc doesn't store grad_fn; inferred from leaf
        # assert_eq(m1.grad_fn is None, m2.grad_fn is None)
        assert_eq(m1.is_sparse, m2.is_sparse)
        if not getattr(tls, "disable_inference_mode", False):
            assert_eq(m1.is_inference, m2.is_inference())
        else:
            assert_eq(m1.is_inference, False)
        assert_eq(m1.is_conj, m2.is_conj())
        assert_eq(m1.is_neg, m2.is_neg())
        assert_eq(m1.grad is not None, safe_grad(m2) is not None)
        if m1.grad is not None:
            go(m1.grad, _expect_safe_grad(m2))
        # TODO: move "assert_eq(m1.layout, m2.layout)" out of sparse
        #       branches (but not ready for prime time yet)...
        if m1.is_sparse:
            assert_eq(m1.layout, m2.layout)
            assert_eq(m1.dense_dim, m2.dense_dim())
            assert_eq(m1.sparse_dim, m2.sparse_dim())
            assert_eq(m1.is_coalesced, m2.is_coalesced())
        elif is_sparse_compressed(m1):
            assert_eq(m1.layout, m2.layout)
            assert_eq(m1.dense_dim, m2.dense_dim())
            assert_eq(m1.sparse_dim, m2.sparse_dim())
        else:
            if not skip_symbolic:
                assert_eq(m1.stride, m2.stride())
                assert_eq(m1.storage_offset, m2.storage_offset())
            assert_eq(m1.is_view, m2._is_view())
            if m1.is_view:
                if m1.base is None:
                    raise AssertionError("m1.base must not be None for a view tensor")
                if m2._base is None:
                    raise AssertionError("m2._base must not be None for a view tensor")
                go(m1.base, m2._base)