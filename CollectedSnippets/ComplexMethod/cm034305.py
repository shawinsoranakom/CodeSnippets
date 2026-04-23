def _early_visit(self, value, value_type) -> _t.Any:
        """Similar to base implementation, but supports an intermediate wrapper for trust inversion."""
        if value_type in (str, _datatag._AnsibleTaggedStr):
            # apply compatibility behavior
            if self.trusted_as_template and self._allow_trust:
                result = _tags.TrustedAsTemplate().tag(value)
            elif self.invert_trust and not _tags.TrustedAsTemplate.is_tagged_on(value) and self._allow_trust:
                result = _Untrusted(value)
            else:
                result = value
        elif value_type is _Untrusted:
            result = value.value
        else:
            result = _json._sentinel

        return result