def validate_ipv46_address(value):
    try:
        validate_ipv4_address(value)
    except ValidationError:
        try:
            validate_ipv6_address(value)
        except ValidationError:
            raise ValidationError(
                _("Enter a valid %(protocol)s address."),
                code="invalid",
                params={"protocol": _("IPv4 or IPv6"), "value": value},
            )