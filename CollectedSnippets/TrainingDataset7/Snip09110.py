def validate_ipv6_address(value):
    if not is_valid_ipv6_address(value):
        raise ValidationError(
            _("Enter a valid %(protocol)s address."),
            code="invalid",
            params={"protocol": _("IPv6"), "value": value},
        )