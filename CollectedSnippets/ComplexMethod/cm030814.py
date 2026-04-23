def test_pickle(self):
        global C  # pickle wants to reference the class by name
        T = TypeVar('T')

        class B(Generic[T]):
            pass

        class C(B[int]):
            pass

        c = C()
        c.foo = 42
        c.bar = 'abc'
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            z = pickle.dumps(c, proto)
            x = pickle.loads(z)
            self.assertEqual(x.foo, 42)
            self.assertEqual(x.bar, 'abc')
            self.assertEqual(x.__dict__, {'foo': 42, 'bar': 'abc'})
        samples = [Any, Union, Tuple, Callable, ClassVar,
                   Union[int, str], ClassVar[List], Tuple[int, ...], Tuple[()],
                   Callable[[str], bytes],
                   typing.DefaultDict, typing.FrozenSet[int]]
        for s in samples:
            for proto in range(pickle.HIGHEST_PROTOCOL + 1):
                z = pickle.dumps(s, proto)
                x = pickle.loads(z)
                self.assertEqual(s, x)
        more_samples = [List, typing.Iterable, typing.Type, List[int],
                        typing.Type[typing.Mapping], typing.AbstractSet[Tuple[int, str]]]
        for s in more_samples:
            for proto in range(pickle.HIGHEST_PROTOCOL + 1):
                z = pickle.dumps(s, proto)
                x = pickle.loads(z)
                self.assertEqual(s, x)

        # Test ParamSpec args and kwargs
        global PP
        PP = ParamSpec('PP')
        for thing in [PP.args, PP.kwargs]:
            for proto in range(pickle.HIGHEST_PROTOCOL + 1):
                with self.subTest(thing=thing, proto=proto):
                    self.assertEqual(
                        pickle.loads(pickle.dumps(thing, proto)),
                        thing,
                    )
        del PP