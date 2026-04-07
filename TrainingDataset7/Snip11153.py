def formfield(self, **kwargs):
        return super().formfield(
            **{
                "min_value": -BigIntegerField.MAX_BIGINT - 1,
                "max_value": BigIntegerField.MAX_BIGINT,
                **kwargs,
            }
        )