def test_builtin_bases(self):
        # Make sure all the builtin types can have their base queried without
        # segfaulting. See issue #5787.
        builtin_types = [tp for tp in builtins.__dict__.values()
                         if isinstance(tp, type)]
        for tp in builtin_types:
            object.__getattribute__(tp, "__bases__")
            if tp is not object:
                if tp is ExceptionGroup:
                    num_bases = 2
                else:
                    num_bases = 1
                self.assertEqual(len(tp.__bases__), num_bases, tp)

        with torch._dynamo.error_on_graph_break(False):
            class L(list):
                pass

            class C(object):
                pass

            class D(C):
                pass

        try:
            L.__bases__ = (dict,)
        except TypeError:
            pass
        else:
            self.fail("shouldn't turn list subclass into dict subclass")

        try:
            list.__bases__ = (dict,)
        except TypeError:
            pass
        else:
            self.fail("shouldn't be able to assign to list.__bases__")

        try:
            D.__bases__ = (C, list)
        except TypeError:
            pass
        else:
            self.fail("best_base calculation found wanting")