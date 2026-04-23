def test_nondtype_nonscalartype(self):
        # See gh-14619 and gh-9505 which introduced the deprecation to fix
        # this. These tests are directly taken from gh-9505
        if np.issubdtype(np.float32, "float64"):
            raise AssertionError("np.float32 should not be subtype of float64")
        if np.issubdtype(np.float32, "f8"):
            raise AssertionError("np.float32 should not be subtype of f8")
        if np.issubdtype(np.int32, "int64"):
            raise AssertionError("np.int32 should not be subtype of int64")
        # for the following the correct spellings are
        # np.integer, np.floating, or np.complexfloating respectively:
        if np.issubdtype(np.int8, int):  # np.int8 is never np.int_
            raise AssertionError("np.int8 should not be subtype of int")
        if np.issubdtype(np.float32, float):
            raise AssertionError("np.float32 should not be subtype of float")
        if np.issubdtype(np.complex64, complex):
            raise AssertionError("np.complex64 should not be subtype of complex")
        if np.issubdtype(np.float32, "float"):
            raise AssertionError("np.float32 should not be subtype of 'float'")
        if np.issubdtype(np.float64, "f"):
            raise AssertionError("np.float64 should not be subtype of 'f'")

        # Test the same for the correct first datatype and abstract one
        # in the case of int, float, complex:
        if not np.issubdtype(np.float64, "float64"):
            raise AssertionError("np.float64 should be subtype of float64")
        if not np.issubdtype(np.float64, "f8"):
            raise AssertionError("np.float64 should be subtype of f8")
        if not np.issubdtype(np.int64, "int64"):
            raise AssertionError("np.int64 should be subtype of int64")
        if not np.issubdtype(np.int8, np.integer):
            raise AssertionError("np.int8 should be subtype of np.integer")
        if not np.issubdtype(np.float32, np.floating):
            raise AssertionError("np.float32 should be subtype of np.floating")
        if not np.issubdtype(np.complex64, np.complexfloating):
            raise AssertionError("np.complex64 should be subtype of np.complexfloating")
        if not np.issubdtype(np.float64, "float"):
            raise AssertionError("np.float64 should be subtype of 'float'")
        if not np.issubdtype(np.float32, "f"):
            raise AssertionError("np.float32 should be subtype of 'f'")