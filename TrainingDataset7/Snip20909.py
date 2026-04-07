def test_bad_iterable(self):
        decorators = {myattr_dec_m, myattr2_dec_m}
        msg = "'set' object is not subscriptable"
        with self.assertRaisesMessage(TypeError, msg):

            @method_decorator(decorators, "method")
            class TestIterable:
                def method(self):
                    "A method"
                    pass