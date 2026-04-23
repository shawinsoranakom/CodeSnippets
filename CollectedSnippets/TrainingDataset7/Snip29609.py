def test_enum_lookup(self):
        class TestEnum(enum.Enum):
            VALUE_1 = "value_1"

        instance = ArrayEnumModel.objects.create(array_of_enums=[TestEnum.VALUE_1])
        self.assertSequenceEqual(
            ArrayEnumModel.objects.filter(array_of_enums__contains=[TestEnum.VALUE_1]),
            [instance],
        )