def to_python(self, value):
        value = super().to_python(value)
        if value:
            # Detect scheme via partition to avoid calling urlsplit() on
            # potentially large or slow-to-normalize inputs.
            scheme, sep, _ = value.partition(":")
            if (
                not sep
                or not scheme
                or not scheme[0].isascii()
                or not scheme[0].isalpha()
                or "/" in scheme
            ):
                # No valid scheme found -- prepend the assumed scheme. Handle
                # scheme-relative URLs ("//example.com") separately.
                if value.startswith("//"):
                    value = self.assume_scheme + ":" + value
                else:
                    value = self.assume_scheme + "://" + value
        return value