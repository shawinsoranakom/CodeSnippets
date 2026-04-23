def test_reduce(self):
        protocols = range(pickle.HIGHEST_PROTOCOL + 1)
        args = (-101, "spam")
        kwargs = {'bacon': -201, 'fish': -301}
        state = {'cheese': -401}

        class C1:
            def __getnewargs__(self):
                return args
        obj = C1()
        for proto in protocols:
            self._check_reduce(proto, obj, args)

        for name, value in state.items():
            setattr(obj, name, value)
        for proto in protocols:
            self._check_reduce(proto, obj, args, state=state)

        class C2:
            def __getnewargs__(self):
                return "bad args"
        obj = C2()
        for proto in protocols:
            if proto >= 2:
                with self.assertRaises(TypeError):
                    obj.__reduce_ex__(proto)

        class C3:
            def __getnewargs_ex__(self):
                return (args, kwargs)
        obj = C3()
        for proto in protocols:
            if proto >= 2:
                self._check_reduce(proto, obj, args, kwargs)

        class C4:
            def __getnewargs_ex__(self):
                return (args, "bad dict")
        class C5:
            def __getnewargs_ex__(self):
                return ("bad tuple", kwargs)
        class C6:
            def __getnewargs_ex__(self):
                return ()
        class C7:
            def __getnewargs_ex__(self):
                return "bad args"
        for proto in protocols:
            for cls in C4, C5, C6, C7:
                obj = cls()
                if proto >= 2:
                    with self.assertRaises((TypeError, ValueError)):
                        obj.__reduce_ex__(proto)

        class C9:
            def __getnewargs_ex__(self):
                return (args, {})
        obj = C9()
        for proto in protocols:
            self._check_reduce(proto, obj, args)

        class C10:
            def __getnewargs_ex__(self):
                raise IndexError
        obj = C10()
        for proto in protocols:
            if proto >= 2:
                with self.assertRaises(IndexError):
                    obj.__reduce_ex__(proto)

        class C11:
            def __getstate__(self):
                return state
        obj = C11()
        for proto in protocols:
            self._check_reduce(proto, obj, state=state)

        class C12:
            def __getstate__(self):
                return "not dict"
        obj = C12()
        for proto in protocols:
            self._check_reduce(proto, obj, state="not dict")

        class C13:
            def __getstate__(self):
                raise IndexError
        obj = C13()
        for proto in protocols:
            with self.assertRaises(IndexError):
                obj.__reduce_ex__(proto)
            if proto < 2:
                with self.assertRaises(IndexError):
                    obj.__reduce__()

        class C14:
            __slots__ = tuple(state)
            def __init__(self):
                for name, value in state.items():
                    setattr(self, name, value)

        obj = C14()
        for proto in protocols:
            if proto >= 2:
                self._check_reduce(proto, obj, state=(None, state))
            else:
                with self.assertRaises(TypeError):
                    obj.__reduce_ex__(proto)
                with self.assertRaises(TypeError):
                    obj.__reduce__()

        class C15(dict):
            pass
        obj = C15({"quebec": -601})
        for proto in protocols:
            self._check_reduce(proto, obj, dictitems=dict(obj))

        class C16(list):
            pass
        obj = C16(["yukon"])
        for proto in protocols:
            self._check_reduce(proto, obj, listitems=list(obj))