def introspected_field_types(self):
        return {
            **super().introspected_field_types,
            "BinaryField": "TextField",
            "BooleanField": "IntegerField",
            "DurationField": "BigIntegerField",
            "GenericIPAddressField": "CharField",
        }