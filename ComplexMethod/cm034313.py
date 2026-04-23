def from_value(cls, value: t.Any) -> SourceContext | None:
        """Attempt to retrieve source and render a contextual indicator from the value's origin (if any)."""
        if value is None:
            return None

        if isinstance(value, Origin):
            origin = value
            value = None
        else:
            origin = Origin.get_tag(value)

        if RedactAnnotatedSourceContext.current(optional=True):
            return cls.error('content redacted')

        if origin and origin.path:
            return cls.from_origin(origin)

        if value is None:
            truncated_value = None
            annotated_source_lines = []
        else:
            # DTFIX-FUTURE: cleanup/share width
            try:
                value = str(value)
            except Exception as ex:
                value = f'<< context unavailable: {ex} >>'

            truncated_value = textwrap.shorten(value, width=120)
            annotated_source_lines = [truncated_value]

        return SourceContext(
            origin=origin or Origin.UNKNOWN,
            annotated_source_lines=annotated_source_lines,
            target_line=truncated_value,
        )