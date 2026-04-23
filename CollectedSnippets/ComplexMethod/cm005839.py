def test_numpy_numeric_serialization(self) -> None:
        """Test serialization of various numpy numeric types."""
        # Test integers
        assert serialize(np.int64(42)) == 42
        assert isinstance(serialize(np.int64(42)), int)

        # Test unsigned integers
        assert serialize(np.uint64(42)) == 42
        assert isinstance(serialize(np.uint64(42)), int)

        # Test floats
        assert serialize(np.float64(math.pi)) == math.pi
        assert isinstance(serialize(np.float64(math.pi)), float)

        # Test float32 (need to account for precision differences)
        float32_val = serialize(np.float32(math.pi))
        assert isinstance(float32_val, float)
        assert abs(float32_val - math.pi) < 1e-6  # Check if close enough

        # Test bool
        assert serialize(np.bool_(True)) is True  # noqa: FBT003
        assert isinstance(serialize(np.bool_(True)), bool)  # noqa: FBT003

        # Test complex numbers
        complex_val = serialize(np.complex64(1 + 2j))
        assert isinstance(complex_val, complex)
        assert abs(complex_val - (1 + 2j)) < 1e-6

        # Test strings
        assert serialize(np.str_("hello")) == "hello"
        assert isinstance(serialize(np.str_("hello")), str)

        # Test bytes
        bytes_val = np.bytes_(b"world")
        assert serialize(bytes_val) == "world"
        assert isinstance(serialize(bytes_val), str)

        # Test unicode
        assert serialize(np.str_("unicode")) == "unicode"
        assert isinstance(serialize(np.str_("unicode")), str)

        # Test object arrays
        obj_array = np.array([1, "two", 3.0], dtype=object)
        result = serialize(obj_array[0])
        assert result == 1
        assert isinstance(result, int)

        result = serialize(obj_array[1])
        assert result == "two"
        assert isinstance(result, str)

        result = serialize(obj_array[2])
        assert result == 3.0
        assert isinstance(result, float)