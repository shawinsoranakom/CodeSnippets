def test_all_repr_eq_any(self):
        objs = (getattr(typing, el) for el in typing.__all__)
        for obj in objs:
            self.assertNotEqual(repr(obj), '')
            self.assertEqual(obj, obj)
            if (getattr(obj, '__parameters__', None)
                    and not isinstance(obj, typing.TypeVar)
                    and isinstance(obj.__parameters__, tuple)
                    and len(obj.__parameters__) == 1):
                self.assertEqual(obj[Any].__args__, (Any,))
            if isinstance(obj, type):
                for base in obj.__mro__:
                    self.assertNotEqual(repr(base), '')
                    self.assertEqual(base, base)