def introspected_field_types(self):
        return {
            **super().introspected_field_types,
            "GenericIPAddressField": "CharField",
            "PositiveBigIntegerField": "BigIntegerField",
            "PositiveIntegerField": "IntegerField",
            "PositiveSmallIntegerField": "IntegerField",
            "SmallIntegerField": "IntegerField",
            "TimeField": "DateTimeField",
        }