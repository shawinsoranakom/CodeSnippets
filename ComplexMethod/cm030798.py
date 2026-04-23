def assert_class_defs_other_unpickle(self, defs, mod, *, fail=False):
        # Unpickle relative to a different module than the original.
        for cls in defs.TOP_CLASSES:
            assert not hasattr(mod, cls.__name__), (cls, getattr(mod, cls.__name__))

        instances = []
        for cls, args in defs.TOP_CLASSES.items():
            with self.subTest(repr(cls)):
                setattr(mod, cls.__name__, cls)
                xid = self.get_xidata(cls)
                inst = cls(*args)
                instxid = self.get_xidata(inst)
                instances.append(
                        (cls, xid, inst, instxid))

        for cls, xid, inst, instxid in instances:
            with self.subTest(repr(cls)):
                delattr(mod, cls.__name__)
                if fail:
                    with self.assertRaises(NotShareableError):
                        _testinternalcapi.restore_crossinterp_data(xid)
                    continue
                got = _testinternalcapi.restore_crossinterp_data(xid)
                self.assertIsNot(got, cls)
                self.assertNotEqual(got, cls)

                gotcls = got
                got = _testinternalcapi.restore_crossinterp_data(instxid)
                self.assertIsNot(got, inst)
                self.assertIs(type(got), gotcls)
                if cls in defs.CLASSES_WITHOUT_EQUALITY:
                    self.assertNotEqual(got, inst)
                elif cls in defs.BUILTIN_SUBCLASSES:
                    self.assertEqual(got, inst)
                else:
                    self.assertNotEqual(got, inst)