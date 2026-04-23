def _validate_attribute(cls, v):
        """Validate attribute."""
        if not v:
            return None

        if v and isinstance(v, list) and not v[0]:
            return None

        attributes = v

        if isinstance(attributes, str):
            attributes = (
                [attributes] if "," not in attributes else attributes.split(",")
            )

        if (
            isinstance(attributes, list)
            and len(attributes) == 1
            and "," in attributes[0]
        ):
            attributes = attributes[0].split(",")

        if not isinstance(attributes, list):
            raise ValueError(
                f"Attribute must be a string or list of strings. Got {type(v)}"
            )

        invalid_attrs = [attr for attr in attributes if attr not in ATTRIBUTES]

        if invalid_attrs:
            raise ValueError(
                f"Invalid attribute(s) '{', '.join(invalid_attrs)}'. Valid attributes are: "
                + ", ".join(sorted(list(ATTRIBUTES)))
            )

        return attributes