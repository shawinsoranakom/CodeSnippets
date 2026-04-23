def testExceptionCleanupState(self):
        # Make sure exception state is cleaned up as soon as the except
        # block is left. See #2507

        with torch._dynamo.error_on_graph_break(False):
            class MyException(Exception):
                def __init__(self, obj):
                    self.obj = obj
            class MyObj:
                pass

        def inner_raising_func():
            # Create some references in exception value and traceback
            local_ref = obj
            raise MyException(obj)

        # Qualified "except" with "as"
        obj = MyObj()
        wr = weakref.ref(obj)
        try:
            inner_raising_func()
        except MyException as e:
            pass
        obj = None
        gc_collect()  # For PyPy or other GCs.
        obj = wr()
        self.assertIsNone(obj)

        # Qualified "except" without "as"
        obj = MyObj()
        wr = weakref.ref(obj)
        try:
            inner_raising_func()
        except MyException:
            pass
        obj = None
        gc_collect()  # For PyPy or other GCs.
        obj = wr()
        self.assertIsNone(obj)

        # Bare "except"
        obj = MyObj()
        wr = weakref.ref(obj)
        try:
            inner_raising_func()
        except:
            pass
        obj = None
        gc_collect()  # For PyPy or other GCs.
        obj = wr()
        self.assertIsNone(obj)

        # "except" with premature block leave
        obj = MyObj()
        wr = weakref.ref(obj)
        for i in [0]:
            try:
                inner_raising_func()
            except:
                break
        obj = None
        gc_collect()  # For PyPy or other GCs.
        obj = wr()
        self.assertIsNone(obj)

        # "except" block raising another exception
        obj = MyObj()
        wr = weakref.ref(obj)
        try:
            try:
                inner_raising_func()
            except:
                raise KeyError
        except KeyError as e:
            # We want to test that the except block above got rid of
            # the exception raised in inner_raising_func(), but it
            # also ends up in the __context__ of the KeyError, so we
            # must clear the latter manually for our test to succeed.
            e.__context__ = None
            obj = None
            gc_collect()  # For PyPy or other GCs.
            obj = wr()
            # guarantee no ref cycles on CPython (don't gc_collect)
            if check_impl_detail(cpython=False):
                gc_collect()
            self.assertIsNone(obj)

        # Some complicated construct
        obj = MyObj()
        wr = weakref.ref(obj)
        try:
            inner_raising_func()
        except MyException:
            try:
                try:
                    raise
                finally:
                    raise
            except MyException:
                pass
        obj = None
        if check_impl_detail(cpython=False):
            gc_collect()
        obj = wr()
        self.assertIsNone(obj)

        # Inside an exception-silencing "with" block
        with torch._dynamo.error_on_graph_break(False):
            class Context:
                def __enter__(self):
                    return self
                def __exit__ (self, exc_type, exc_value, exc_tb):
                    return True
        obj = MyObj()
        wr = weakref.ref(obj)
        with Context():
            inner_raising_func()
        obj = None
        if check_impl_detail(cpython=False):
            gc_collect()
        obj = wr()
        self.assertIsNone(obj)