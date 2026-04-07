def as_sql(self, compiler, connection):
        connection.ops.check_expression_support(self)
        start, end = self.window_frame_start_end(
            connection, self.start.value, self.end.value
        )
        if self.exclusion and not connection.features.supports_frame_exclusion:
            raise NotSupportedError(
                "This backend does not support window frame exclusions."
            )
        return (
            self.template
            % {
                "frame_type": self.frame_type,
                "start": start,
                "end": end,
                "exclude": self.get_exclusion(),
            },
            (),
        )