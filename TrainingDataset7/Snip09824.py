def introspected_field_types(self):
        return {
            **super().introspected_field_types,
            "PositiveBigIntegerField": "BigIntegerField",
            "PositiveIntegerField": "IntegerField",
            "PositiveSmallIntegerField": "SmallIntegerField",
        }