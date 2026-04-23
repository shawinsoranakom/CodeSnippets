def test_acquire_many_impl_locks_with_timeout(
        self,
        impl_typename_combos: tuple[str, ...],
    ) -> None:
        impls: list[impls._CacheImpl] = []
        for impl_typename in impl_typename_combos:
            impl: impls._CacheImpl = self.impl_from_typename(impl_typename)
            impls.append(impl)

        with locks._acquire_many_impl_locks_with_timeout(*impls):
            for impl in impls:
                if hasattr(impl, "_lock"):
                    self.assertTrue(impl._lock.locked())
                elif hasattr(impl, "_flock"):
                    self.assertTrue(impl._flock.is_locked)

        for impl in impls:
            if hasattr(impl, "_lock"):
                self.assertFalse(impl._lock.locked())
            elif hasattr(impl, "_flock"):
                self.assertFalse(impl._flock.is_locked)