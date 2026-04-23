def _parse_recursive_coerce_types_and_tag(self, value: t.Any) -> t.Any:
        if isinstance(value, str):
            return TrustedAsTemplate().tag(self._origin.tag(value))
        if isinstance(value, (list, tuple, set)):
            # NB: intentional coercion of tuple/set to list, deal with it
            return self._origin.tag([self._parse_recursive_coerce_types_and_tag(v) for v in value])
        if isinstance(value, dict):
            # FIXME: enforce keys are strings
            return self._origin.tag({self._origin.tag(k): self._parse_recursive_coerce_types_and_tag(v) for k, v in value.items()})

        if value is ...:  # literal_eval parses ellipsis, but it's not a supported variable type
            value = TrustedAsTemplate().tag("...")

        if isinstance(value, complex):  # convert unsupported variable types recognized by literal_eval back to str
            value = TrustedAsTemplate().tag(str(value))

        value = to_text(value, nonstring='passthru', errors='surrogate_or_strict')

        return self._origin.tag(value)