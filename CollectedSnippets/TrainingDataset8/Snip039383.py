def test_different_enums(self):
        """Different enum classes should have different hashes, even when the enum
        values are the same."""

        class EnumClassA(Enum):
            ENUM_1 = "hello"

        class EnumClassB(Enum):
            ENUM_1 = "hello"

        enum_a = EnumClassA.ENUM_1
        enum_b = EnumClassB.ENUM_1

        self.assertNotEqual(get_hash(enum_a), get_hash(enum_b))