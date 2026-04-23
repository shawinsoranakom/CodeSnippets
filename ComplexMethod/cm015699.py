def test_errors(self):
        # Testing errors...
        try:
            with torch._dynamo.error_on_graph_break(False):
                class C(list, dict):
                    pass
        except TypeError:
            pass
        else:
            self.fail("inheritance from both list and dict should be illegal")

        try:
            with torch._dynamo.error_on_graph_break(False):
                class C(object, None):
                    pass
        except TypeError:
            pass
        else:
            self.fail("inheritance from non-type should be illegal")
        with torch._dynamo.error_on_graph_break(False):
            class Classic:
                pass

        try:
            with torch._dynamo.error_on_graph_break(False):
                class C(type(len)):
                    pass
        except TypeError:
            pass
        else:
            self.fail("inheritance from CFunction should be illegal")

        try:
            with torch._dynamo.error_on_graph_break(False):
                class C(object):
                    __slots__ = 1
        except TypeError:
            pass
        else:
            self.fail("__slots__ = 1 should be illegal")

        try:
            with torch._dynamo.error_on_graph_break(False):
                class C(object):
                    __slots__ = [1]
        except TypeError:
            pass
        else:
            self.fail("__slots__ = [1] should be illegal")

        with torch._dynamo.error_on_graph_break(False):
            class M1(type):
                pass
            class M2(type):
                pass
            class A1(object, metaclass=M1):
                pass
            class A2(object, metaclass=M2):
                pass
        try:
            with torch._dynamo.error_on_graph_break(False):
                class B(A1, A2):
                    pass
        except TypeError:
            pass
        else:
            self.fail("finding the most derived metaclass should have failed")