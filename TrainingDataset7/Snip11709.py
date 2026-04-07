def as_oracle(self, compiler, connection, **extra_context):
        if (
            self.output_field.get_internal_type() == "DurationField"
            and not connection.features.supports_aggregation_over_interval_types
        ):
            expression = self.get_source_expressions()[0]
            options = self._get_repr_options()
            from django.db.backends.oracle.functions import (
                IntervalToSeconds,
                SecondsToInterval,
            )

            return compiler.compile(
                SecondsToInterval(
                    self.__class__(IntervalToSeconds(expression), **options)
                )
            )
        return super().as_sql(compiler, connection, **extra_context)