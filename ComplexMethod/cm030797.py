def assert_equal_or_equalish(self, obj, expected):
        cls = type(expected)
        if cls.__eq__ is not object.__eq__:
            self.assertEqual(obj, expected)
        elif cls is types.FunctionType:
            self.assert_functions_equal(obj, expected)
        elif isinstance(expected, BaseException):
            self.assert_exc_equal(obj, expected)
        elif cls is types.MethodType:
            raise NotImplementedError(cls)
        elif cls is types.BuiltinMethodType:
            raise NotImplementedError(cls)
        elif cls is types.MethodWrapperType:
            raise NotImplementedError(cls)
        elif cls.__bases__ == (object,):
            self.assertEqual(obj.__dict__, expected.__dict__)
        else:
            raise NotImplementedError(cls)