def test_subtype(self):
        from torch.utils.data.datapipes._typing import issubtype

        basic_type = (int, str, bool, float, complex, list, tuple, dict, set, T_co)
        for t in basic_type:
            self.assertTrue(issubtype(t, t))
            self.assertTrue(issubtype(t, Any))
            if t == T_co:
                self.assertTrue(issubtype(Any, t))
            else:
                self.assertFalse(issubtype(Any, t))
        for t1, t2 in itertools.product(basic_type, basic_type):
            if t1 == t2 or t2 == T_co:
                self.assertTrue(issubtype(t1, t2))
            else:
                self.assertFalse(issubtype(t1, t2))

        T = TypeVar("T", int, str)
        S = TypeVar("S", bool, str | int, tuple[int, T])  # type: ignore[valid-type]
        types = (
            (int, Optional[int]),  # noqa: UP045
            (list, Union[int, list]),  # noqa: UP007
            (tuple[int, str], S),
            (tuple[int, str], tuple),
            (T, S),
            (S, T_co),
            (T, Union[S, set]),  # noqa: UP007
        )
        for sub, par in types:
            self.assertTrue(issubtype(sub, par))
            self.assertFalse(issubtype(par, sub))

        subscriptable_types = {
            list: 1,
            tuple: 2,  # use 2 parameters
            set: 1,
            dict: 2,
        }
        for subscript_type, n in subscriptable_types.items():
            for ts in itertools.combinations(types, n):
                subs, pars = zip(*ts)
                sub = subscript_type[subs]  # type: ignore[index]
                par = subscript_type[pars]  # type: ignore[index]
                self.assertTrue(issubtype(sub, par))
                self.assertFalse(issubtype(par, sub))
                # Non-recursive check
                self.assertTrue(issubtype(par, sub, recursive=False))