def test_enum(self):
        """The hashing function returns the same result when called with the same
        Enum members."""

        class EnumClass(Enum):
            ENUM_1 = auto()
            ENUM_2 = auto()

        # Hash values should be stable
        self.assertEqual(get_hash(EnumClass.ENUM_1), get_hash(EnumClass.ENUM_1))

        # Different enum values should produce different hashes
        self.assertNotEqual(get_hash(EnumClass.ENUM_1), get_hash(EnumClass.ENUM_2))